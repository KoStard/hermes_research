import sys
import pytest
import uuid
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.hermes_research.utils.paths.paths_manager import PathsManager

class TestPathsManager:
    
    @pytest.fixture
    def paths_manager(self):
        return PathsManager()
    
    def test_getResearchSessionPath_returnsExpectedPath_withValidInputs(self, paths_manager):
        """Test that get_research_session_path correctly combines parent directory and session name."""
        research_dir = "/home/user/research"
        session_name = "test_session"
        expected_path = str(Path(research_dir) / session_name)
        
        result = paths_manager.get_research_session_path(research_dir, session_name)
        
        assert result == expected_path
    
    def test_getResearchSessionPath_handlesSpecialCharacters_inSessionName(self, paths_manager):
        """Test that get_research_session_path correctly handles special characters in session name."""
        research_dir = "/home/user/research"
        session_name = "test session-with!special@chars#"
        expected_path = str(Path(research_dir) / session_name)
        
        result = paths_manager.get_research_session_path(research_dir, session_name)
        
        assert result == expected_path
    
    @patch('uuid.uuid4')
    def test_getRemoteFilesFolder_returnsUniquePaths_onMultipleCalls(self, mock_uuid4, paths_manager):
        """Test that get_remote_files_folder returns unique paths on multiple calls."""
        mock_uuid4.side_effect = [
            MagicMock(spec=uuid.UUID, __str__=lambda _: "abc-123"),
            MagicMock(spec=uuid.UUID, __str__=lambda _: "def-456")
        ]
        
        path1 = paths_manager.get_remote_files_folder()
        path2 = paths_manager.get_remote_files_folder()
        
        assert path1 != path2
        assert path1 == f"/tmp/{PathsManager.APP_NAME}/abc-123/"
        assert path2 == f"/tmp/{PathsManager.APP_NAME}/def-456/"
    
    @patch('uuid.uuid4')
    def test_getRemoteFilesFolder_returnsCorrectFormat_forRemoteTemporaryPath(self, mock_uuid4, paths_manager):
        """Test that get_remote_files_folder returns path in the expected format."""
        mock_uuid4.return_value = MagicMock(spec=uuid.UUID, __str__=lambda _: "abc-123")
        
        path = paths_manager.get_remote_files_folder()
        
        # Should be in format /tmp/hermes_research/{uuid}/
        assert path == f"/tmp/{PathsManager.APP_NAME}/abc-123/"
        assert path.startswith("/tmp/")
        assert path.endswith("/")
    
    @patch('pathlib.Path.resolve')
    def test_getAbsolutePath_normalizesPath_forRelativePath(self, mock_resolve, paths_manager):
        """Test that get_absolute_path correctly normalizes a relative path."""
        relative_path = "research/data"
        expected_absolute_path = "/normalized/research/data"
        mock_resolve.return_value = Path(expected_absolute_path)
        
        result = paths_manager.get_absolute_path(relative_path)
        
        assert result == expected_absolute_path
        mock_resolve.assert_called_once()
    
    @patch('pathlib.Path.resolve')
    def test_getAbsolutePath_preservesAbsolutePath_forAbsolutePath(self, mock_resolve, paths_manager):
        """Test that get_absolute_path preserves an absolute path after normalization."""
        if sys.platform == 'win32':
            absolute_path = "C:\\Users\\test\\research"
            expected_path = "C:\\Users\\test\\normalized"
        else:
            absolute_path = "/home/user/research"
            expected_path = "/home/user/normalized"
            
        mock_resolve.return_value = Path(expected_path)
        
        result = paths_manager.get_absolute_path(absolute_path)
        
        assert result == expected_path
        mock_resolve.assert_called_once()
