import subprocess
import logging
import shlex
from typing import Optional, List, Dict
from . import SSHConnectionInterface, SSHDestination

logger = logging.getLogger(__name__)

class SSHError(Exception):
    """Base exception for SSH-related errors."""
    pass

class SSHConnectionError(SSHError):
    """Exception raised when SSH connection fails."""
    pass

class SSHCommandError(SSHError):
    """Exception raised when command execution fails."""
    pass

class SSHTimeoutError(SSHError):
    """Exception raised when SSH operations timeout."""
    pass

class SubprocessSSHConnection(SSHConnectionInterface):
    """Implements SSH connection operations using the subprocess module."""
    
    def __init__(self, timeout: int = 30, options: Optional[Dict[str, str]] = None):
        """
        Initialize the SSH connection handler with custom options.
        
        Args:
            timeout: Default timeout in seconds for SSH operations.
            options: Optional dictionary of SSH options to include with each command.
                     Example: {'StrictHostKeyChecking': 'no', 'IdentityFile': '~/.ssh/id_rsa'}
        """
        self.timeout = timeout
        self.options = options or {}
        
    def _build_ssh_command(self, destination: SSHDestination, remote_command: Optional[str] = None) -> List[str]:
        """
        Builds the SSH command with all options.
        
        Args:
            destination: The SSH destination details.
            remote_command: Optional command to execute on the remote host.
            
        Returns:
            A list of command parts to pass to subprocess.
        """
        ssh_command = ["ssh"]
        
        # Add any custom SSH options
        for key, value in self.options.items():
            ssh_command.extend(["-o", f"{key}={value}"])
            
        # Add the destination
        ssh_command.append(f"{destination.username}@{destination.hostname}")
        
        # Add the remote command if provided
        if remote_command is not None:
            ssh_command.append(remote_command)
            
        return ssh_command

    def test_connection(self, destination: SSHDestination) -> bool:
        """
        Tests the SSH connection to the specified destination.

        Args:
            destination: The SSH destination details.

        Returns:
            True if the connection is successful, False otherwise.
        """
        ssh_command = self._build_ssh_command(destination, "exit")  # Simple command to check connectivity
        
        try:
            logger.debug(f"Testing SSH connection with command: {' '.join(ssh_command)}")
            result = subprocess.run(
                ssh_command, 
                check=False, 
                capture_output=True, 
                text=True, 
                timeout=self.timeout,
            )
            
            if result.returncode == 0:
                logger.info(f"SSH connection to {destination.username}@{destination.hostname} successful.")
                return True
            else:
                err_msg = result.stderr.strip()
                
                # Check for common SSH errors and provide more specific logging
                if "Permission denied" in err_msg:
                    logger.warning(f"SSH authentication failed for {destination.username}@{destination.hostname}. Check credentials.")
                elif "Host key verification failed" in err_msg:
                    logger.warning(f"SSH host key verification failed for {destination.hostname}. This might be a first-time connection.")
                elif "Could not resolve hostname" in err_msg:
                    logger.warning(f"Could not resolve hostname {destination.hostname}. Check network and DNS.")
                elif "Connection refused" in err_msg:
                    logger.warning(f"Connection refused to {destination.hostname}. Check if SSH service is running.")
                elif "Operation timed out" in err_msg:
                    logger.warning(f"Connection timed out to {destination.hostname}. Check network connectivity.")
                else:
                    logger.warning(f"SSH connection test failed to {destination.username}@{destination.hostname}. Return code: {result.returncode}")
                
                logger.debug(f"SSH stderr: {err_msg}")
                return False
                
        except FileNotFoundError:
            logger.error("SSH command not found. Please ensure OpenSSH client is installed and in PATH.")
            return False
        except subprocess.TimeoutExpired:
            logger.warning(f"SSH connection test timed out for {destination.username}@{destination.hostname}.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during SSH connection test: {e}")
            return False

    def execute_command_on_remote(self, command: str, destination: SSHDestination) -> tuple[str, str, int]:
        """
        Executes a command on the remote server via SSH.

        Args:
            command: The command string to execute remotely.
            destination: The SSH destination details.

        Returns:
            A tuple containing (stdout, stderr, return_code).

        Raises:
            FileNotFoundError: If the ssh command is not found.
            SSHConnectionError: If SSH connection fails with authentication or host key issues.
            SSHCommandError: If the remote command execution fails.
            SSHTimeoutError: If the operation times out.
            Exception: For other potential errors during execution.
        """
        # Safely escape the command to prevent shell injection issues
        ssh_command = self._build_ssh_command(destination, command)
        
        try:
            logger.debug(f"Executing remote command: {' '.join(ssh_command)}")
            result = subprocess.run(
                ssh_command, 
                check=False, 
                capture_output=True, 
                text=True,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Remote command executed successfully on {destination.username}@{destination.hostname}.")
            else:
                err_msg = result.stderr.strip()
                logger.warning(f"Remote command failed on {destination.username}@{destination.hostname}. Command: '{command}'. Return code: {result.returncode}")
                
                # Provide more specific error information
                if "Permission denied" in err_msg:
                    logger.warning(f"SSH authentication failed for {destination.username}@{destination.hostname}.")
                elif "Host key verification failed" in err_msg:
                    logger.warning(f"SSH host key verification failed for {destination.hostname}.")
                
                logger.debug(f"Stderr: {err_msg}")

            logger.debug(f"Remote command stdout: {result.stdout}")
            
            return result.stdout, result.stderr, result.returncode

        except FileNotFoundError:
            error_msg = "SSH command not found. Please ensure OpenSSH client is installed and in PATH."
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {self.timeout} seconds on {destination.hostname}"
            logger.error(error_msg)
            raise SSHTimeoutError(error_msg)
            
        except Exception as e:
            error_msg = f"An unexpected error occurred during remote command execution: {e}"
            logger.error(error_msg)
            raise SSHCommandError(error_msg) from e
