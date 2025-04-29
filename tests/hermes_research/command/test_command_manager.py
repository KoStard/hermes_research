import os
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
        extra_args = ""

        # Act
        result = command_manager.generate_command(path_to_research, model, files, budget, prompt, extra_args)

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
        extra_args = ""

        # Act
        result = command_manager.generate_command(path_to_research, model, files, budget, prompt, extra_args)

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
        extra_args = ""

        # Act
        result = command_manager.generate_command(path_to_research, model, files, budget, prompt, extra_args)

        # Assert
        expected_command = """hermes chat \\
    --model bedrock/us.anthropic.claude-3-7-sonnet-20250219-v1:0 \\
    --deep-research /path/to/new-deep-research/directory \\
    --set_deep_research_budget 20 \\
    --text "Test prompt with \\"quotes\\" and special \\$characters\""""
        assert result == expected_command

    def test_generateCommand_includesExtraArguments_whenProvided(self, command_manager):
        """Test that generate_command includes extra arguments when they are provided."""
        # Arrange
        path_to_research = "/path/to/research"
        model = "test-model"
        files = ["/path/to/file1.txt"]
        budget = 50
        prompt = "Base prompt"
        extra_args = '--another-arg "value" --flag'

        # Act
        result = command_manager.generate_command(path_to_research, model, files, budget, prompt, extra_args)

        # Assert
        expected_command = """hermes chat \\
    --model test-model \\
    --deep-research /path/to/research \\
    --set_deep_research_budget 50 \\
    --text "Base prompt" \\
    --textual_file "/path/to/file1.txt" \\
    --another-arg "value" --flag"""
        assert result == expected_command
        
    def test_saveCommandInFile_savesContent_toSpecifiedPath(self, command_manager, tmp_path):
        """Test that the command is correctly saved to the specified file path."""
        # Arrange
        command = "hermes chat --model claude-3-opus --deep-research /path/to/research"
        file_path = str(tmp_path / "test_command.sh")
        
        # Act
        command_manager.save_command_in_file(command, file_path)
        
        # Assert
        assert os.path.exists(file_path)
        with open(file_path, 'r') as f:
            content = f.read()
        assert content == command

    def test_saveCommandInFile_createsDirectories_whenNotExisting(self, command_manager, tmp_path):
        """Test that directories are created if they don't exist."""
        # Arrange
        command = "hermes chat --model claude-3-opus"
        nested_dir = tmp_path / "nested" / "dirs"
        file_path = str(nested_dir / "test_command.sh")
        
        # Act
        command_manager.save_command_in_file(command, file_path)
        
        # Assert
        assert os.path.exists(file_path)
        with open(file_path, 'r') as f:
            content = f.read()
        assert content == command

    def test_saveCommandInFile_handlesSpecialCharacters_inCommandString(self, command_manager, tmp_path):
        """Test that special characters in the command are properly saved."""
        # Arrange
        command = 'hermes chat --text "Complex prompt with $special & \\"quoted\\" characters"'
        file_path = str(tmp_path / "special_command.sh")
        
        # Act
        command_manager.save_command_in_file(command, file_path)
        
        # Assert
        with open(file_path, 'r') as f:
            content = f.read()
        assert content == command
