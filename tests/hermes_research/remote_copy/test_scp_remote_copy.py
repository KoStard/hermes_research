import os
import logging
import pytest
import subprocess
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from hermes_research.remote_copy.scp_remote_copy import SCPRemoteCopy
from hermes_research.tmux.ssh.subprocess_ssh_connection import SSHCommandError, SSHTimeoutError
from hermes_research.tmux.ssh import SSHDestination

class TestSCPRemoteCopy:
    
    @pytest.fixture
    def mock_ssh_connection(self):
        """Create a mock SSHConnectionInterface."""
        mock = MagicMock()
        # Default behavior for successful operations
        mock.execute_command_on_remote.return_value = ("", "", 0)
        return mock
    
    @pytest.fixture
    def scp_remote_copy(self, mock_ssh_connection):
        """Create an SCPRemoteCopy instance with mock SSH connection."""
        return SCPRemoteCopy(mock_ssh_connection)
    
    @pytest.fixture
    def ssh_destination(self):
        """Create a test SSH destination."""
        return SSHDestination(username="testuser", hostname="testhost")
    
    @pytest.fixture
    def mock_file_exists(self):
        """Patch os.path.isfile to return True for test files."""
        with patch('os.path.isfile', return_value=True) as mock:
            yield mock
    
    def test_remoteCopyFiles_createsDirectoriesAndCopiesFiles_whenValidInput(
        self, scp_remote_copy, mock_ssh_connection, ssh_destination, mock_file_exists
    ):
        """Test successful file copying with directory creation."""
        # Arrange
        source_to_target = {
            "/local/path/file1.txt": "/remote/path/file1.txt",
            "/local/path/file2.txt": "/remote/path/subdir/file2.txt"
        }
        
        # Act
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stderr = ""
            scp_remote_copy.remote_copy_files(source_to_target, ssh_destination)
        
        # Assert
        # Check directory creation commands
        mock_ssh_connection.execute_command_on_remote.assert_any_call(
            "mkdir -p /remote/path", ssh_destination
        )
        mock_ssh_connection.execute_command_on_remote.assert_any_call(
            "mkdir -p /remote/path/subdir", ssh_destination
        )
        
        # Check file copy commands
        mock_run.assert_any_call(
            ["scp", "/local/path/file1.txt", "testuser@testhost:/remote/path/file1.txt"],
            check=False, capture_output=True, text=True, timeout=60
        )
        mock_run.assert_any_call(
            ["scp", "/local/path/file2.txt", "testuser@testhost:/remote/path/subdir/file2.txt"],
            check=False, capture_output=True, text=True, timeout=60
        )
    
    def test_remoteCopyFiles_raisesFileNotFoundError_whenSourceFileDoesNotExist(
        self, scp_remote_copy, ssh_destination
    ):
        """Test error handling for non-existent source files."""
        # Arrange
        source_to_target = {
            "/nonexistent/file.txt": "/remote/path/file.txt"
        }
        
        # Act & Assert
        with patch('os.path.isfile', return_value=False):
            with pytest.raises(FileNotFoundError) as excinfo:
                scp_remote_copy.remote_copy_files(source_to_target, ssh_destination)
            
            assert "Source file not found" in str(excinfo.value)
    
    def test_remoteCopyFiles_raisesSSHCommandError_whenDirectoryCreationFails(
        self, scp_remote_copy, mock_ssh_connection, ssh_destination, mock_file_exists
    ):
        """Test error handling when remote directory creation fails."""
        # Arrange
        source_to_target = {
            "/local/path/file.txt": "/remote/path/file.txt"
        }
        mock_ssh_connection.execute_command_on_remote.return_value = ("", "Permission denied", 1)
        
        # Act & Assert
        with pytest.raises(SSHCommandError) as excinfo:
            scp_remote_copy.remote_copy_files(source_to_target, ssh_destination)
            
        assert "Failed to create remote directory" in str(excinfo.value)
    
    def test_remoteCopyFiles_raisesSSHCommandError_whenSCPCommandFails(
        self, scp_remote_copy, mock_ssh_connection, ssh_destination, mock_file_exists
    ):
        """Test error handling when SCP command fails."""
        # Arrange
        source_to_target = {
            "/local/path/file.txt": "/remote/path/file.txt"
        }
        
        # Act & Assert
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "Permission denied"
            
            with pytest.raises(SSHCommandError) as excinfo:
                scp_remote_copy.remote_copy_files(source_to_target, ssh_destination)
                
            assert "SCP command failed" in str(excinfo.value)
    
    def test_remoteCopyFiles_raisesFileNotFoundError_whenSCPCommandNotFound(
        self, scp_remote_copy, mock_ssh_connection, ssh_destination, mock_file_exists
    ):
        """Test error handling when SCP command is not found."""
        # Arrange
        source_to_target = {
            "/local/path/file.txt": "/remote/path/file.txt"
        }
        
        # Act & Assert
        with patch('subprocess.run', side_effect=FileNotFoundError("No such file or directory: 'scp'")):
            with pytest.raises(FileNotFoundError) as excinfo:
                scp_remote_copy.remote_copy_files(source_to_target, ssh_destination)
                
            assert "SCP command not found" in str(excinfo.value)
    
    def test_remoteCopyFiles_raisesSSHTimeoutError_whenSCPOperationTimesOut(
        self, scp_remote_copy, mock_ssh_connection, ssh_destination, mock_file_exists
    ):
        """Test error handling when SCP operation times out."""
        # Arrange
        source_to_target = {
            "/local/path/file.txt": "/remote/path/file.txt"
        }
        
        # Act & Assert
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("scp", 60)):
            with pytest.raises(SSHTimeoutError) as excinfo:
                scp_remote_copy.remote_copy_files(source_to_target, ssh_destination)
                
            assert "SCP operation timed out" in str(excinfo.value)
    
    def test_remoteCopyFiles_handlesSpecialCharacters_inFileNames(
        self, scp_remote_copy, mock_ssh_connection, ssh_destination, mock_file_exists
    ):
        """Test handling of special characters in file names."""
        # Arrange
        source_to_target = {
            "/local/path/file with spaces.txt": "/remote/path/file with spaces.txt",
            "/local/path/file-with-dashes.txt": "/remote/path/file-with-dashes.txt"
        }
        
        # Act
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            scp_remote_copy.remote_copy_files(source_to_target, ssh_destination)
        
        # Assert
        mock_run.assert_any_call(
            ["scp", "/local/path/file with spaces.txt", "testuser@testhost:/remote/path/file with spaces.txt"],
            check=False, capture_output=True, text=True, timeout=60
        )
    
    def test_remoteCopyFiles_usesCustomTimeout_whenSpecified(
        self, mock_ssh_connection, ssh_destination, mock_file_exists
    ):
        """Test custom timeout value is used."""
        # Arrange
        custom_timeout = 30
        scp_remote_copy = SCPRemoteCopy(mock_ssh_connection, timeout=custom_timeout)
        source_to_target = {
            "/local/path/file.txt": "/remote/path/file.txt"
        }
        
        # Act
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            scp_remote_copy.remote_copy_files(source_to_target, ssh_destination)
        
        # Assert
        mock_run.assert_called_with(
            ["scp", "/local/path/file.txt", "testuser@testhost:/remote/path/file.txt"],
            check=False, capture_output=True, text=True, timeout=custom_timeout
        )
    
    def test_remoteCopyFiles_handlesNoRemoteDirectories_whenTargetHasNoPath(
        self, scp_remote_copy, mock_ssh_connection, ssh_destination, mock_file_exists
    ):
        """Test handling when target paths have no directories."""
        # Arrange
        source_to_target = {
            "/local/path/file.txt": "file.txt"  # No directory in target
        }
        
        # Act
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            scp_remote_copy.remote_copy_files(source_to_target, ssh_destination)
        
        # Assert
        # Should not call mkdir since there's no directory to create
        assert mock_ssh_connection.execute_command_on_remote.call_count == 0
        
        # Should still copy the file
        mock_run.assert_called_with(
            ["scp", "/local/path/file.txt", "testuser@testhost:file.txt"],
            check=False, capture_output=True, text=True, timeout=60
        )
