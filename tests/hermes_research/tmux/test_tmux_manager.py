import pytest
from unittest.mock import MagicMock, patch
import subprocess
import os

from hermes_research.tmux.tmux_manager import TmuxManager, _UnsetTmuxEnv
from hermes_research.tmux.ssh import SSHConnectionInterface, SSHDestination


class TestTmuxManager:
    
    @pytest.fixture
    def mock_ssh_connection(self):
        """Create a mock SSHConnectionInterface."""
        mock = MagicMock(spec=SSHConnectionInterface)
        # Default behavior for test_connection is success
        mock.test_connection.return_value = True
        return mock
    
    @pytest.fixture
    def tmux_manager(self, mock_ssh_connection):
        """Create a TmuxManager with the mock SSH connection."""
        return TmuxManager(ssh_connection=mock_ssh_connection)
    
    @pytest.fixture
    def ssh_destination(self):
        """Create a test SSHDestination."""
        return SSHDestination(username="testuser", hostname="testhost.example.com")
    
    def test_setRemote_configuresRemoteOperation_withValidDestination(
        self, tmux_manager, ssh_destination, mock_ssh_connection
    ):
        """Test that set_remote properly configures the manager for remote operations."""
        # Act
        tmux_manager.set_remote(ssh_destination)
        
        # Assert
        assert tmux_manager._remote_destination == ssh_destination
        assert tmux_manager._ssh_connection == mock_ssh_connection
    
    def test_setRemote_raisesException_whenNoSSHConnectionProvided(self, ssh_destination):
        """Test that set_remote raises an error if no SSH connection was provided."""
        # Arrange
        tmux_manager = TmuxManager()  # No SSH connection provided
        
        # Act & Assert
        with pytest.raises(ValueError, match="SSH connection handler not provided"):
            tmux_manager.set_remote(ssh_destination)
    
    def test_listSessions_returnsSessionsFromRemoteHost_whenRemoteConfigured(
        self, tmux_manager, ssh_destination, mock_ssh_connection
    ):
        """Test that list_sessions returns sessions from the remote host when configured."""
        # Arrange
        tmux_manager.set_remote(ssh_destination)
        expected_sessions = ["session1", "session2", "research"]
        mock_ssh_connection.execute_command_on_remote.return_value = (
            "\n".join(expected_sessions) + "\n",  # stdout
            "",  # stderr
            0   # return code
        )
        
        # Act
        result = tmux_manager.list_sessions()
        
        # Assert
        assert result == expected_sessions
        mock_ssh_connection.execute_command_on_remote.assert_called_once()
        # Check that the correct command was passed
        cmd_arg = mock_ssh_connection.execute_command_on_remote.call_args[1]["command"]
        assert "tmux list-sessions -F" in cmd_arg
    
    def test_listSessions_returnsEmptyList_whenRemoteHasNoSessions(
        self, tmux_manager, ssh_destination, mock_ssh_connection
    ):
        """Test that list_sessions returns an empty list when remote has no sessions."""
        # Arrange
        tmux_manager.set_remote(ssh_destination)
        mock_ssh_connection.execute_command_on_remote.return_value = (
            "",  # stdout
            "no server running",  # stderr
            1    # return code for error
        )
        
        # Act
        result = tmux_manager.list_sessions()
        
        # Assert
        assert result == []
    
    def test_sessionExists_returnsTrue_whenRemoteSessionExists(
        self, tmux_manager, ssh_destination, mock_ssh_connection
    ):
        """Test that session_exists returns True when the session exists on remote."""
        # Arrange
        tmux_manager.set_remote(ssh_destination)
        session_name = "research"
        mock_ssh_connection.execute_command_on_remote.return_value = (
            "session1\nresearch\nsession2\n",  # stdout
            "",  # stderr
            0   # return code
        )
        
        # Act
        result = tmux_manager.session_exists(session_name)
        
        # Assert
        assert result is True
    
    def test_sessionExists_returnsFalse_whenRemoteSessionDoesNotExist(
        self, tmux_manager, ssh_destination, mock_ssh_connection
    ):
        """Test that session_exists returns False when the session doesn't exist on remote."""
        # Arrange
        tmux_manager.set_remote(ssh_destination)
        session_name = "nonexistent"
        mock_ssh_connection.execute_command_on_remote.return_value = (
            "session1\nsession2\n",  # stdout
            "",  # stderr
            0   # return code
        )
        
        # Act
        result = tmux_manager.session_exists(session_name)
        
        # Assert
        assert result is False
    
    def test_createSession_createsSessionOnRemoteHost_whenRemoteConfigured(
        self, tmux_manager, ssh_destination, mock_ssh_connection
    ):
        """Test that create_session creates a session on the remote host."""
        # Arrange
        tmux_manager.set_remote(ssh_destination)
        session_name = "new_research"
        mock_ssh_connection.execute_command_on_remote.return_value = (
            "",  # stdout
            "",  # stderr
            0   # return code (success)
        )
        
        # Act
        tmux_manager.create_session(session_name)
        
        # Assert
        mock_ssh_connection.execute_command_on_remote.assert_called_once()
        # Check that the correct command was passed
        cmd_arg = mock_ssh_connection.execute_command_on_remote.call_args[1]["command"]
        assert f"tmux new-session -d -s {session_name}" in cmd_arg
    
    def test_createSession_raisesError_whenRemoteCreationFails(
        self, tmux_manager, ssh_destination, mock_ssh_connection
    ):
        """Test that create_session raises an error when remote creation fails."""
        # Arrange
        tmux_manager.set_remote(ssh_destination)
        session_name = "invalid*name"  # Name with invalid character
        mock_ssh_connection.execute_command_on_remote.return_value = (
            "",  # stdout
            "invalid session name",  # stderr
            1   # return code (failure)
        )
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to create tmux session"):
            tmux_manager.create_session(session_name)
    
    def test_sendCommand_sendsCommandToRemoteSession_whenRemoteConfigured(
        self, tmux_manager, ssh_destination, mock_ssh_connection
    ):
        """Test that send_command sends a command to the remote session."""
        # Arrange
        tmux_manager.set_remote(ssh_destination)
        session_name = "research"
        command = "hermes --model gpt-4 --prompt 'test'"
        mock_ssh_connection.execute_command_on_remote.return_value = (
            "",  # stdout
            "",  # stderr
            0   # return code (success)
        )
        
        # Act
        tmux_manager.send_command(session_name, command)
        
        # Assert
        mock_ssh_connection.execute_command_on_remote.assert_called_once()
        # Check that the correct command was passed
        cmd_arg = mock_ssh_connection.execute_command_on_remote.call_args[1]["command"]
        assert "tmux send-keys -t research" in cmd_arg
    
    def test_sendCommand_raisesError_whenRemoteSendFails(
        self, tmux_manager, ssh_destination, mock_ssh_connection
    ):
        """Test that send_command raises an error when remote send fails."""
        # Arrange
        tmux_manager.set_remote(ssh_destination)
        session_name = "nonexistent"
        command = "hermes --model gpt-4 --prompt 'test'"
        mock_ssh_connection.execute_command_on_remote.return_value = (
            "",  # stdout
            "can't find session nonexistent",  # stderr
            1   # return code (failure)
        )
        
        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to send command to tmux session"):
            tmux_manager.send_command(session_name, command)
    
    def test_killSession_killsRemoteSession_whenRemoteConfigured(
        self, tmux_manager, ssh_destination, mock_ssh_connection
    ):
        """Test that kill_session kills the remote session."""
        # Arrange
        tmux_manager.set_remote(ssh_destination)
        session_name = "research"
        mock_ssh_connection.execute_command_on_remote.return_value = (
            "",  # stdout
            "",  # stderr
            0   # return code (success)
        )
        
        # Act
        tmux_manager.kill_session(session_name)
        
        # Assert
        mock_ssh_connection.execute_command_on_remote.assert_called_once()
        # Check that the correct command was passed
        cmd_arg = mock_ssh_connection.execute_command_on_remote.call_args[1]["command"]
        assert f"tmux kill-session -t {session_name}" in cmd_arg
    
    def test_killSession_handlesNonexistentSession_whenRemoteConfigured(
        self, tmux_manager, ssh_destination, mock_ssh_connection
    ):
        """Test that kill_session handles nonexistent session on remote."""
        # Arrange
        tmux_manager.set_remote(ssh_destination)
        session_name = "nonexistent"
        mock_ssh_connection.execute_command_on_remote.return_value = (
            "",  # stdout
            "can't find session nonexistent",  # stderr
            1   # return code (failure)
        )
        
        # Act - should not raise an exception
        tmux_manager.kill_session(session_name)
        
        # Assert
        mock_ssh_connection.execute_command_on_remote.assert_called_once()
        
    def test_executeTmuxCommand_handlesSSHException_duringRemoteExecution(
        self, tmux_manager, ssh_destination, mock_ssh_connection
    ):
        """Test that _execute_tmux_command handles SSH exceptions during remote execution."""
        # Arrange
        tmux_manager.set_remote(ssh_destination)
        mock_ssh_connection.execute_command_on_remote.side_effect = Exception("SSH connection failed")
        
        # Act
        stdout, stderr, return_code = tmux_manager._execute_tmux_command(["list-sessions"])
        
        # Assert
        assert stdout == ""
        assert "SSH connection failed" in stderr
        assert return_code == -1
        
    # Test for the _UnsetTmuxEnv context manager
    def test_unsetTmuxEnv_unsetsAndRestoresTmuxVariable_whenUsed(self):
        """Test that _UnsetTmuxEnv correctly unsets and restores the TMUX environment variable."""
        # Arrange
        original_value = "original_value"
        os.environ["TMUX"] = original_value
        
        # Act
        with _UnsetTmuxEnv():
            # Inside the context, TMUX should be unset
            assert "TMUX" not in os.environ
        
        # Assert - After the context, TMUX should be restored
        assert os.environ["TMUX"] == original_value
        
        # Clean up
        if "TMUX" in os.environ:
            del os.environ["TMUX"]
