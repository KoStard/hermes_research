import pytest
import subprocess
from unittest.mock import MagicMock, patch, call
import logging

from hermes_research.tmux.ssh import SSHDestination
from hermes_research.tmux.ssh.subprocess_ssh_connection import (
    SubprocessSSHConnection, 
    SSHError, 
    SSHConnectionError,
    SSHCommandError,
    SSHTimeoutError
)


class TestSubprocessSSHConnection:
    
    @pytest.fixture
    def ssh_connection(self):
        """Create a SubprocessSSHConnection instance."""
        return SubprocessSSHConnection()
    
    @pytest.fixture
    def mock_subprocess_run(self):
        """Mock the subprocess.run function."""
        with patch('subprocess.run') as mock_run:
            # Configure a default successful response
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "command output"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            yield mock_run
            
    @pytest.fixture
    def test_destination(self):
        """Create a test SSHDestination."""
        return SSHDestination(username="testuser", hostname="testhost.example.com")
    
    def test_buildSshCommand_includesBasicElements_withNoOptions(self, ssh_connection, test_destination):
        """Test that _build_ssh_command generates the correct basic command."""
        # Act
        result = ssh_connection._build_ssh_command(test_destination)
        
        # Assert
        assert result == ["ssh", "testuser@testhost.example.com"]
    
    def test_buildSshCommand_includesRemoteCommand_whenProvided(self, ssh_connection, test_destination):
        """Test that _build_ssh_command includes the remote command when provided."""
        # Act
        result = ssh_connection._build_ssh_command(test_destination, "echo hello")
        
        # Assert
        assert result == ["ssh", "testuser@testhost.example.com", "echo hello"]
    
    def test_buildSshCommand_includesCustomOptions_whenProvided(self):
        """Test that _build_ssh_command includes custom SSH options."""
        # Arrange
        ssh_connection = SubprocessSSHConnection(options={
            "StrictHostKeyChecking": "no", 
            "IdentityFile": "~/.ssh/id_rsa"
        })
        destination = SSHDestination(username="testuser", hostname="testhost.example.com")
        
        # Act
        result = ssh_connection._build_ssh_command(destination)
        
        # Assert
        assert "-o" in result
        assert "StrictHostKeyChecking=no" in result
        assert "IdentityFile=~/.ssh/id_rsa" in result
        assert "testuser@testhost.example.com" in result
    
    def test_testConnection_returnsTrue_whenSshSuccessful(
        self, ssh_connection, mock_subprocess_run, test_destination
    ):
        """Test that test_connection returns True when SSH connection is successful."""
        # Arrange
        mock_subprocess_run.return_value.returncode = 0
        
        # Act
        result = ssh_connection.test_connection(test_destination)
        
        # Assert
        assert result is True
        mock_subprocess_run.assert_called_once()
    
    def test_testConnection_returnsFalse_whenSshFails(
        self, ssh_connection, mock_subprocess_run, test_destination
    ):
        """Test that test_connection returns False when SSH connection fails."""
        # Arrange
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "Permission denied"
        
        # Act
        result = ssh_connection.test_connection(test_destination)
        
        # Assert
        assert result is False
        mock_subprocess_run.assert_called_once()
    
    def test_testConnection_returnsFalse_whenAuthenticationFails(
        self, ssh_connection, mock_subprocess_run, test_destination
    ):
        """Test that test_connection returns False when authentication fails."""
        # Arrange
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "Permission denied (publickey,password,keyboard-interactive)."
        
        # Act
        result = ssh_connection.test_connection(test_destination)
        
        # Assert
        assert result is False
        mock_subprocess_run.assert_called_once()
    
    def test_testConnection_returnsFalse_whenHostKeyVerificationFails(
        self, ssh_connection, mock_subprocess_run, test_destination
    ):
        """Test that test_connection returns False when host key verification fails."""
        # Arrange
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "Host key verification failed."
        
        # Act
        result = ssh_connection.test_connection(test_destination)
        
        # Assert
        assert result is False
        mock_subprocess_run.assert_called_once()
    
    def test_testConnection_returnsFalse_whenHostnameResolutionFails(
        self, ssh_connection, mock_subprocess_run, test_destination
    ):
        """Test that test_connection returns False when hostname resolution fails."""
        # Arrange
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stderr = "Could not resolve hostname testhost.example.com"
        
        # Act
        result = ssh_connection.test_connection(test_destination)
        
        # Assert
        assert result is False
        mock_subprocess_run.assert_called_once()
    
    def test_testConnection_returnsFalse_whenConnectionTimeout(
        self, ssh_connection, mock_subprocess_run, test_destination
    ):
        """Test that test_connection returns False when connection times out."""
        # Arrange
        mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=30)
        
        # Act
        result = ssh_connection.test_connection(test_destination)
        
        # Assert
        assert result is False
        mock_subprocess_run.assert_called_once()
    
    def test_testConnection_returnsFalse_whenSshNotFound(
        self, ssh_connection, mock_subprocess_run, test_destination
    ):
        """Test that test_connection returns False when SSH command is not found."""
        # Arrange
        mock_subprocess_run.side_effect = FileNotFoundError()
        
        # Act
        result = ssh_connection.test_connection(test_destination)
        
        # Assert
        assert result is False
        mock_subprocess_run.assert_called_once()
    
    def test_executeCommandOnRemote_returnsCorrectTuple_whenCommandSucceeds(
        self, ssh_connection, mock_subprocess_run, test_destination
    ):
        """Test that execute_command_on_remote returns the correct tuple when command succeeds."""
        # Arrange
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "command output\n"
        mock_subprocess_run.return_value.stderr = ""
        
        # Act
        stdout, stderr, returncode = ssh_connection.execute_command_on_remote("echo hello", test_destination)
        
        # Assert
        assert stdout == "command output\n"
        assert stderr == ""
        assert returncode == 0
        mock_subprocess_run.assert_called_once()
    
    def test_executeCommandOnRemote_returnsCorrectTuple_whenCommandFails(
        self, ssh_connection, mock_subprocess_run, test_destination
    ):
        """Test that execute_command_on_remote returns the correct tuple when command fails."""
        # Arrange
        mock_subprocess_run.return_value.returncode = 1
        mock_subprocess_run.return_value.stdout = ""
        mock_subprocess_run.return_value.stderr = "command not found\n"
        
        # Act
        stdout, stderr, returncode = ssh_connection.execute_command_on_remote("invalid_command", test_destination)
        
        # Assert
        assert stdout == ""
        assert stderr == "command not found\n"
        assert returncode == 1
        mock_subprocess_run.assert_called_once()
    
    def test_executeCommandOnRemote_raisesFileNotFoundError_whenSshNotFound(
        self, ssh_connection, mock_subprocess_run, test_destination
    ):
        """Test that execute_command_on_remote raises FileNotFoundError when SSH command is not found."""
        # Arrange
        mock_subprocess_run.side_effect = FileNotFoundError()
        
        # Act & Assert
        with pytest.raises(FileNotFoundError):
            ssh_connection.execute_command_on_remote("echo hello", test_destination)
        
        mock_subprocess_run.assert_called_once()
    
    def test_executeCommandOnRemote_raisesSSHTimeoutError_whenCommandTimesOut(
        self, ssh_connection, mock_subprocess_run, test_destination
    ):
        """Test that execute_command_on_remote raises SSHTimeoutError when command times out."""
        # Arrange
        mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="ssh", timeout=30)
        
        # Act & Assert
        with pytest.raises(SSHTimeoutError):
            ssh_connection.execute_command_on_remote("sleep 60", test_destination)
        
        mock_subprocess_run.assert_called_once()
    
    def test_executeCommandOnRemote_raisesSSHCommandError_whenUnexpectedErrorOccurs(
        self, ssh_connection, mock_subprocess_run, test_destination
    ):
        """Test that execute_command_on_remote raises SSHCommandError when an unexpected error occurs."""
        # Arrange
        mock_subprocess_run.side_effect = Exception("Unexpected error")
        
        # Act & Assert
        with pytest.raises(SSHCommandError):
            ssh_connection.execute_command_on_remote("echo hello", test_destination)
        
        mock_subprocess_run.assert_called_once()
    
    def test_executeCommandOnRemote_handlesCommandWithSpecialCharacters(
        self, ssh_connection, mock_subprocess_run, test_destination
    ):
        """Test that execute_command_on_remote properly handles commands with special characters."""
        # Arrange
        command = "echo 'Hello; World' && echo \"Test > file\""
        
        # Act
        ssh_connection.execute_command_on_remote(command, test_destination)
        
        # Assert
        mock_subprocess_run.assert_called_once()
        # Verify the command was passed correctly to ssh
        cmd_args = mock_subprocess_run.call_args[0][0]
        assert cmd_args[-1] == command
        
    def test_customTimeout_usesSpecifiedTimeout_whenProvidedToConstructor(
        self, mock_subprocess_run, test_destination
    ):
        """Test that a custom timeout is used when provided to the constructor."""
        # Arrange
        custom_timeout = 60
        ssh_connection = SubprocessSSHConnection(timeout=custom_timeout)
        
        # Act
        ssh_connection.test_connection(test_destination)
        
        # Assert
        mock_subprocess_run.assert_called_once()
        assert mock_subprocess_run.call_args[1]["timeout"] == custom_timeout
