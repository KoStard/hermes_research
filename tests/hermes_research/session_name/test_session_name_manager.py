import pytest
from unittest.mock import MagicMock, patch

from hermes_research.session_name.session_name_manager import SessionNameManager

class TestSessionNameManager:
    
    @pytest.fixture
    def mock_tmux_manager(self):
        """Create a mock TmuxManager."""
        return MagicMock()
    
    @pytest.fixture
    def session_name_manager(self, mock_tmux_manager):
        """Create a SessionNameManager with a mock TmuxManager."""
        return SessionNameManager(tmux_manager=mock_tmux_manager)
    
    def test_handleSessionNameConflict_returnsOriginalName_whenNoConflict(self, session_name_manager, mock_tmux_manager):
        """Test that original name is returned when no session exists with that name."""
        # Arrange
        mock_tmux_manager.session_exists.return_value = False
        session_name = "test_session"
        
        # Act
        result = session_name_manager.handle_session_name_conflict(session_name)
        
        # Assert
        assert result == session_name
        mock_tmux_manager.session_exists.assert_called_once_with(session_name)
    
    @patch('hermes_research.session_name.session_name_manager.MenuManager.selection_menu')
    @patch('hermes_research.session_name.session_name_manager.logger')
    def test_handleSessionNameConflict_killsExistingSession_whenUserChoosesToKill(
        self, mock_logger, mock_selection_menu, session_name_manager, mock_tmux_manager
    ):
        """Test that existing session is killed when user chooses that option."""
        # Arrange
        mock_tmux_manager.session_exists.side_effect = [True, False]  # First check true, second check false
        mock_selection_menu.return_value = 0  # User selected "Kill existing session"
        session_name = "existing_session"
        
        # Act
        result = session_name_manager.handle_session_name_conflict(session_name)
        
        # Assert
        assert result == session_name
        mock_tmux_manager.kill_session.assert_called_once_with(session_name)
        assert mock_logger.info.call_count >= 1
    
    @patch('hermes_research.session_name.session_name_manager.MenuManager.selection_menu')
    @patch('hermes_research.session_name.session_name_manager.MenuManager.text_prompt')
    @patch('hermes_research.session_name.session_name_manager.logger')
    def test_handleSessionNameConflict_usesNewName_whenUserProvidesValidAlternative(
        self, mock_logger, mock_text_prompt, mock_selection_menu, session_name_manager, mock_tmux_manager
    ):
        """Test that a new name is used when user provides a valid alternative."""
        # Arrange
        original_name = "existing_session"
        new_name = "new_session"
        
        # Session exists check: First true for original, then false for new name
        mock_tmux_manager.session_exists.side_effect = lambda name: name == original_name
        
        mock_selection_menu.return_value = 1  # User selected "Enter a new session name"
        mock_text_prompt.return_value = new_name
        
        # Act
        result = session_name_manager.handle_session_name_conflict(original_name)
        
        # Assert
        assert result == new_name
        assert mock_logger.warning.call_count >= 1  # Warning about research directory
    
    @patch('hermes_research.session_name.session_name_manager.MenuManager.selection_menu')
    @patch('hermes_research.session_name.session_name_manager.logger')
    def test_handleSessionNameConflict_raisesKeyboardInterrupt_whenUserCancels(
        self, mock_logger, mock_selection_menu, session_name_manager, mock_tmux_manager
    ):
        """Test that KeyboardInterrupt is raised when user cancels."""
        # Arrange
        mock_tmux_manager.session_exists.return_value = True
        mock_selection_menu.return_value = 2  # User selected "Cancel"
        session_name = "test_session"
        
        # Act/Assert
        with pytest.raises(KeyboardInterrupt):
            session_name_manager.handle_session_name_conflict(session_name)
        
        assert mock_logger.warning.call_count >= 1
        assert mock_logger.info.call_count >= 1
    
    @patch('hermes_research.session_name.session_name_manager.MenuManager.selection_menu')
    @patch('hermes_research.session_name.session_name_manager.logger')
    def test_handleSessionNameConflict_addsServerContext_whenRemote(
        self, mock_logger, mock_selection_menu, session_name_manager, mock_tmux_manager
    ):
        """Test that server context is added to messages for remote sessions."""
        # Arrange
        mock_tmux_manager.session_exists.side_effect = [True, False]  # First check true, then false
        mock_selection_menu.return_value = 0  # User selected "Kill existing session"
        session_name = "remote_session"
        server_name = "test-server"
        
        # Act
        result = session_name_manager.handle_session_name_conflict(session_name, is_remote=True, server_name=server_name)
        
        # Assert
        assert result == session_name
        
        # Verify server context was included in messages
        menu_calls = mock_selection_menu.call_args_list
        assert len(menu_calls) == 1
        menu_text = menu_calls[0][0][0]  # First positional arg to first call
        assert f"on server '{server_name}'" in menu_text
