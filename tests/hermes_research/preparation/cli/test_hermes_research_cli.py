import os
import pytest
from argparse import Namespace
from unittest.mock import MagicMock, patch, call

from hermes_research.preparation.cli.hermes_research_cli import HermesResearchCLI
from hermes_research.preparation.menu import MenuSelection
from hermes_research.preparation.config import HermesConfig, HermesConfigRemoteServer
from hermes_research.tmux.ssh import SSHDestination

class TestHermesResearchCLI:
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mocked dependencies for the CLI."""
        deps = {
            "paths_manager": MagicMock(),
            "config_manager": MagicMock(),
            "menu": MagicMock(),
            "command_manager": MagicMock(),
            "tmux_manager": MagicMock(),
            "remote_copy": MagicMock(),
            "ssh_connection": MagicMock(),
            "session_name_manager": MagicMock()
        }
        
        # Configure session_name_manager to return the same session name that's passed to it
        deps["session_name_manager"].handle_session_name_conflict.side_effect = lambda name, **kwargs: name
        # Set up common return values
        deps["paths_manager"].get_absolute_path.side_effect = lambda p: f"/absolute/path/to/{p}"
        deps["paths_manager"].get_research_session_path.return_value = "/research/path/test_session"
        deps["paths_manager"].get_remote_files_folder.return_value = "/tmp/hermes_research/uuid"
        
        deps["command_manager"].generate_command.return_value = "hermes chat --model test"
        deps["command_manager"].create_temp_script.return_value = "/tmp/hermes_script.sh"
        
        # Set up config
        mock_config = HermesConfig(
            research_directory="/research/dir",
            default_budget=30,
            models=["test-model", "other-model"],
            remote_servers={
                "test-server": HermesConfigRemoteServer(
                    hostname="test.example.com",
                    username="testuser",
                    remote_research_path="/remote/research"
                )
            }
        )
        deps["config_manager"].load_config.return_value = mock_config
        
        # Set up menu selection
        deps["menu"].get_selection.return_value = MenuSelection(
            session_name="test_session",
            model="test-model",
            budget=30,
            prompt="Test prompt",
            selected_server_name=None  # Default to local execution
        )
        
        return deps
    
    @pytest.fixture
    def cli(self, mock_dependencies):
        """Create a CLI instance with mocked dependencies."""
        return HermesResearchCLI(**mock_dependencies)
    
    @pytest.fixture
    def args(self):
        """Create mock CLI arguments."""
        return Namespace(
            files=["test.txt", "data.csv"],
            command_args="--temperature 0.7"
        )
    
    @pytest.fixture
    def remote_selection(self, mock_dependencies):
        """Create a menu selection for remote execution."""
        mock_dependencies["menu"].get_selection.return_value = MenuSelection(
            session_name="remote_session",
            model="test-model",
            budget=50,
            prompt="Remote test prompt",
            selected_server_name="test-server"
        )
        # Configure SSH connection success
        mock_dependencies["ssh_connection"].test_connection.return_value = True
        mock_dependencies["ssh_connection"].execute_command_on_remote.return_value = ("", "", 0)
        
        return mock_dependencies["menu"].get_selection.return_value
    
    def test_defineCli_addsExpectedArguments_whenCalled(self):
        """Test CLI argument definition."""
        parser = MagicMock()
        cli = HermesResearchCLI(
            paths_manager=MagicMock(),
            config_manager=MagicMock(),
            menu=MagicMock(),
            command_manager=MagicMock(),
            tmux_manager=MagicMock(),
            remote_copy=MagicMock(),
            ssh_connection=MagicMock(),
            session_name_manager=MagicMock()
        )
        
        cli.define_cli(parser)
        
        # Should call add_argument twice - once for files and once for command_args
        assert parser.add_argument.call_count == 2
        # Check command_args argument
        assert any("command-args" in str(call) for call in parser.add_argument.call_args_list)
    
    def test_execute_runsLocalFlow_whenLocalExecutionSelected(self, cli, mock_dependencies, args):
        """Test the local execution flow."""
        # Execute with local flow (default in fixture)
        cli.execute(args)
        
        # Check that paths were resolved
        mock_dependencies["paths_manager"].get_absolute_path.assert_any_call("test.txt")
        mock_dependencies["paths_manager"].get_absolute_path.assert_any_call("data.csv")
        
        # Check research path was obtained
        mock_dependencies["paths_manager"].get_research_session_path.assert_called_once()
        
        # Check command was generated with correct params
        mock_dependencies["command_manager"].generate_command.assert_called_with(
            path_to_research="/research/path/test_session",
            model="test-model",
            files=["/absolute/path/to/test.txt", "/absolute/path/to/data.csv"],
            budget=30,
            prompt="Test prompt",
            extra_arguments="--temperature 0.7"
        )
        
        # Check tmux operations
        mock_dependencies["tmux_manager"].set_remote.assert_called_with(None)
        
        # Get the actual argument passed to create_session without strict matching
        mock_dependencies["tmux_manager"].create_session.assert_called()
        # Get the session name that was actually used
        session_name_arg = mock_dependencies["tmux_manager"].create_session.call_args[0][0]
        
        mock_dependencies["tmux_manager"].send_command.assert_called_with(
            session_name_arg,  # Use the actual session name that was passed
            f". /tmp/hermes_script.sh"
        )
    
    def test_execute_handlesSessionNameConflict_inLocalFlow(self, cli, mock_dependencies, args):
        """Test that session name conflicts are handled in local flow."""
        # Set this specific test to return a different name
        mock_dependencies["session_name_manager"].handle_session_name_conflict.return_value = "test_session_new"
        mock_dependencies["session_name_manager"].handle_session_name_conflict.side_effect = None
        
        # Execute
        cli.execute(args)
        
        # Check session_name_manager was called with correct params
        mock_dependencies["session_name_manager"].handle_session_name_conflict.assert_called_with(
            "test_session", is_remote=False
        )
        
        # Check tmux was created with the new name
        mock_dependencies["tmux_manager"].create_session.assert_called_with("test_session_new")
        mock_dependencies["tmux_manager"].send_command.assert_called_with(
            "test_session_new", 
            f". /tmp/hermes_script.sh"
        )
    
    def test_execute_stopsExecution_whenNoResearchDirectory(self, cli, mock_dependencies, args):
        """Test that execution stops if research directory is not configured."""
        # Set empty research directory
        config = mock_dependencies["config_manager"].load_config.return_value
        config.research_directory = ""
        
        # Execute
        cli.execute(args)
        
        # Check that tmux operations were not called
        mock_dependencies["tmux_manager"].create_session.assert_not_called()
    
    def test_execute_runsRemoteFlow_whenRemoteServerSelected(self, cli, mock_dependencies, args, remote_selection):
        """Test the remote execution flow."""
        # Execute with remote flow
        cli.execute(args)
        
        # Check SSH connection was tested
        mock_dependencies["ssh_connection"].test_connection.assert_called()
        
        # Check remote directory was created
        mock_dependencies["ssh_connection"].execute_command_on_remote.assert_any_call(
            "mkdir -p /tmp/hermes_research/uuid", 
            SSHDestination(username="testuser", hostname="test.example.com")
        )
        
        # Check files were copied
        mock_dependencies["remote_copy"].remote_copy_files.assert_called()
        
        # Check tmux was configured for remote
        mock_dependencies["tmux_manager"].set_remote.assert_called_with(
            SSHDestination(username="testuser", hostname="test.example.com")
        )
        
        # Check remote session was created
        mock_dependencies["tmux_manager"].create_session.assert_called()
        
        # Get the session name that was actually used
        session_name_arg = mock_dependencies["tmux_manager"].create_session.call_args[0][0]
        
        # Check command was sent to remote tmux
        mock_dependencies["tmux_manager"].send_command.assert_called_with(
            session_name_arg,  # Use the actual session name that was passed
            f"bash /tmp/hermes_research/uuid/run_research.sh"
        )
    
    def test_execute_handlesSSHConnectionFailure_inRemoteFlow(self, cli, mock_dependencies, args, remote_selection):
        """Test handling of SSH connection failure in remote flow."""
        # Set SSH connection test to fail
        mock_dependencies["ssh_connection"].test_connection.return_value = False
        
        # Execute
        cli.execute(args)
        
        # Check that file operations were not attempted
        mock_dependencies["remote_copy"].remote_copy_files.assert_not_called()
        mock_dependencies["tmux_manager"].create_session.assert_not_called()
    
    def test_execute_handlesRemoteTmuxFailure_inRemoteFlow(self, cli, mock_dependencies, args, remote_selection):
        """Test handling of tmux failure in remote flow."""
        # Setup tmux to raise an exception
        mock_dependencies["tmux_manager"].create_session.side_effect = RuntimeError("Tmux error")
        
        # Execute
        cli.execute(args)
        
        # Check that send_command was not called after the failure
        mock_dependencies["tmux_manager"].send_command.assert_not_called()
    
    def test_execute_handlesFileCopyFailure_inRemoteFlow(self, cli, mock_dependencies, args, remote_selection):
        """Test handling of file copy failure in remote flow."""
        # Setup remote_copy to raise an exception
        mock_dependencies["remote_copy"].remote_copy_files.side_effect = Exception("Copy failed")
        
        # Execute
        cli.execute(args)
        
        # Check that tmux operations were not attempted
        mock_dependencies["tmux_manager"].create_session.assert_not_called()
    
    def test_execute_cleansTempScript_afterRemoteExecution(self, cli, mock_dependencies, args, remote_selection):
        """Test that temporary script is cleaned up after remote execution."""
        # Mock os path exists and unlink
        with patch('os.path.exists', return_value=True) as mock_exists:
            with patch('os.unlink') as mock_unlink:
                # Execute
                cli.execute(args)
                
                # Check that temp script was checked for existence and removed
                mock_exists.assert_called_with("/tmp/hermes_script.sh")
                mock_unlink.assert_called_with("/tmp/hermes_script.sh")
    
    def test_execute_handlesUserCancellation_whenSessionNameConflictOccurs(self, cli, mock_dependencies, args):
        """Test handling of user cancellation during session name resolution."""
        # Setup session_name_manager to raise KeyboardInterrupt
        mock_dependencies["session_name_manager"].handle_session_name_conflict.side_effect = KeyboardInterrupt()
        
        # Execute
        cli.execute(args)
        
        # Check that tmux operations were not attempted
        mock_dependencies["tmux_manager"].create_session.assert_not_called()
