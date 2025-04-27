import pytest
from unittest.mock import patch, mock_open
from hermes_research.command.command_manager import HermesResearchCommandManager


class TestHermesResearchCommandManager:
    
    @pytest.fixture
    def command_manager(self):
        return HermesResearchCommandManager()
    
    def test_generateCommand_returnsFormattedCommand_withValidInputs(self, command_manager):
        """Test that generate_command returns a properly formatted command string when given valid inputs."""
        # Arrange
        path_to_research = "/path/to/new-deep-research/directory"
        model = "bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        files = ["/path/to/file1.md", "/path/to/file2.md"]
        budget = 30
        prompt = "This is a test prompt"
        
        # Act
        result = command_manager.generate_command(path_to_research, model, files, budget, prompt)
        
        # Assert
        expected_command = """hermes chat \\
    --model bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0 \\
    --deep-research /path/to/new-deep-research/directory \\
    --set_deep_research_budget 30 \\
    --text "This is a test prompt" \\
    --textual_file "/path/to/file1.md" \\
    --textual_file "/path/to/file2.md\""""
        assert result == expected_command
    
    def test_generateCommand_handlesEmptyFilesList_withValidPrompt(self, command_manager):
        """Test that generate_command works correctly with empty files list."""
        # Arrange
        path_to_research = "/path/to/new-deep-research/directory"
        model = "bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        files = []
        budget = 10
        prompt = "Test prompt with no files"
        
        # Act
        result = command_manager.generate_command(path_to_research, model, files, budget, prompt)
        
        # Assert
        expected_command = """hermes chat \\
    --model bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0 \\
    --deep-research /path/to/new-deep-research/directory \\
    --set_deep_research_budget 10 \\
    --text "Test prompt with no files\""""
        assert result == expected_command
    
    def test_generateCommand_escapesSpecialCharacters_inPrompt(self, command_manager):
        """Test that generate_command properly escapes quotes and special characters in the prompt."""
        # Arrange
        path_to_research = "/path/to/new-deep-research/directory"
        model = "bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        files = []
        budget = 20
        prompt = 'Test prompt with "quotes" and special $characters'
        
        # Act
        result = command_manager.generate_command(path_to_research, model, files, budget, prompt)
        
        # Assert
        expected_command = """hermes chat \\
    --model bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0 \\
    --deep-research /path/to/new-deep-research/directory \\
    --set_deep_research_budget 20 \\
    --text "Test prompt with \\"quotes\\" and special \\$characters\""""
        assert result == expected_command
    
    def test_saveCommandInFile_writesCommand_toSpecifiedPath(self, command_manager):
        """Test that save_command_in_file writes the command to the specified file."""
        # Arrange
        command = 'hermes chat --model bedrock/model-id --text "Test command"'
        path = "/tmp/test_command.sh"
        
        # Act/Assert
        with patch("builtins.open", mock_open()) as mock_file:
            command_manager.save_command_in_file(command, path)
            mock_file.assert_called_once_with(path, 'w')
            mock_file().write.assert_called_once_with(command)
    
    def test_saveCommandInFile_createsDirectories_whenPathDoesntExist(self, command_manager):
        """Test that save_command_in_file creates necessary directories if they don't exist."""
        # Arrange
        command = 'hermes chat --text "Test command"'
        path = "/non/existing/directory/test_command.sh"
        
        # Act/Assert
        with patch("os.path.dirname") as mock_dirname, \
             patch("os.path.exists") as mock_exists, \
             patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_open()) as mock_file:
            
            mock_dirname.return_value = "/non/existing/directory"
            mock_exists.return_value = False
            
            command_manager.save_command_in_file(command, path)
            
            mock_exists.assert_called_once_with("/non/existing/directory")
            mock_makedirs.assert_called_once_with("/non/existing/directory")
            mock_file.assert_called_once_with(path, 'w')
            mock_file().write.assert_called_once_with(command)
