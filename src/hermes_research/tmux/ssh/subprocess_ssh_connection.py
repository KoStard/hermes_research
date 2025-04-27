import subprocess
import logging
from . import SSHConnectionInterface, SSHDestination

logger = logging.getLogger(__name__)

class SubprocessSSHConnection(SSHConnectionInterface):
    """Implements SSH connection operations using the subprocess module."""

    def test_connection(self, destination: SSHDestination) -> bool:
        """
        Tests the SSH connection to the specified destination.

        Args:
            destination: The SSH destination details.

        Returns:
            True if the connection is successful, False otherwise.
        """
        ssh_command = [
            "ssh",
            f"{destination.username}@{destination.hostname}",
            "exit"  # Simple command to check connectivity
        ]
        try:
            logger.debug(f"Testing SSH connection with command: {' '.join(ssh_command)}")
            result = subprocess.run(ssh_command, check=False, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"SSH connection to {destination.username}@{destination.hostname} successful.")
                return True
            else:
                logger.warning(f"SSH connection test failed to {destination.username}@{destination.hostname}. Return code: {result.returncode}")
                logger.debug(f"SSH stderr: {result.stderr}")
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
            Exception: For other potential errors during execution.
        """
        ssh_command = [
            "ssh",
            f"{destination.username}@{destination.hostname}",
            command # The command to execute remotely
        ]
        try:
            logger.debug(f"Executing remote command: {' '.join(ssh_command)}")
            # Using check=False to capture output even on failure
            result = subprocess.run(ssh_command, check=False, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Remote command executed successfully on {destination.username}@{destination.hostname}.")
            else:
                 logger.warning(f"Remote command failed on {destination.username}@{destination.hostname}. Command: '{command}'. Return code: {result.returncode}")
                 logger.warning(f"Stderr: {result.stderr}")

            logger.debug(f"Remote command stdout: {result.stdout}")
            logger.debug(f"Remote command stderr: {result.stderr}")
            
            return result.stdout, result.stderr, result.returncode

        except FileNotFoundError:
            logger.error("SSH command not found. Please ensure OpenSSH client is installed and in PATH.")
            # Re-raise the exception as it indicates a setup problem
            raise 
        except Exception as e:
            logger.error(f"An unexpected error occurred during remote command execution: {e}")
            # Re-raise other unexpected exceptions
            raise
