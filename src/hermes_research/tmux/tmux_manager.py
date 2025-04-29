import logging
import os
import shlex
import subprocess
from typing import List, Optional

from . import TmuxManagerInterface
from .ssh import SSHConnectionInterface, SSHDestination

logger = logging.getLogger(__name__)


class _UnsetTmuxEnv:
    """Context manager for temporarily unsetting the TMUX environment variable."""

    def __enter__(self):
        self.original_value = os.environ.get("TMUX")
        if "TMUX" in os.environ:
            logger.debug("Temporarily unsetting TMUX environment variable.")
            del os.environ["TMUX"]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_value is not None:
            logger.debug("Restoring TMUX environment variable.")
            os.environ["TMUX"] = self.original_value
        elif "TMUX" in os.environ:
            # If it was set during the context, ensure it's removed if it wasn't there originally
            del os.environ["TMUX"]


class TmuxManager(TmuxManagerInterface):
    """Manages tmux sessions, potentially remotely via SSH."""

    def __init__(self, ssh_connection: Optional[SSHConnectionInterface] = None):
        """
        Initializes the TmuxManager.

        Args:
            ssh_connection: An optional SSH connection interface for remote operations.
        """
        self._ssh_connection = ssh_connection
        self._remote_destination: Optional[SSHDestination] = None
        logger.debug("TmuxManager initialized.")

    def set_remote(self, destination: SSHDestination):
        """
        Configures the manager to operate on a remote tmux server via SSH.

        Args:
            destination: The SSH destination details.
        """
        if not self._ssh_connection:
            logger.error("Cannot set remote mode without an SSHConnectionInterface instance.")
            raise ValueError("SSH connection handler not provided during initialization.")
        self._remote_destination = destination
        logger.info(f"TmuxManager configured for remote operations on {destination.username}@{destination.hostname}")

    def _execute_tmux_command(self, command_args: List[str]) -> tuple[str, str, int]:
        """Executes a tmux command locally or remotely."""
        base_command = ["tmux"] + command_args

        if self._remote_destination and self._ssh_connection:
            # Execute remotely
            full_command_str = shlex.join(base_command)
            logger.debug(f"Executing remote tmux command: {full_command_str} on {self._remote_destination.username}@{self._remote_destination.hostname}")
            try:
                stdout, stderr, return_code = self._ssh_connection.execute_command_on_remote(
                    command=full_command_str,
                    destination=self._remote_destination
                )
                if return_code != 0:
                     logger.warning(f"Remote tmux command failed. Code: {return_code}, Stderr: {stderr.strip()}")
                return stdout, stderr, return_code
            except Exception as e:
                logger.error(f"Failed to execute remote tmux command: {e}")
                return "", str(e), -1 # Indicate failure with a non-zero code
        else:
            # Execute locally
            logger.debug(f"Executing local tmux command: {shlex.join(base_command)}")
            try:
                # Unset TMUX env var to allow running tmux commands inside tmux
                with _UnsetTmuxEnv():
                    result = subprocess.run(base_command, capture_output=True, text=True, check=False)
                if result.returncode != 0:
                    logger.warning(f"Local tmux command failed. Code: {result.returncode}, Stderr: {result.stderr.strip()}")
                return result.stdout, result.stderr, result.returncode
            except FileNotFoundError:
                logger.error("tmux command not found. Please ensure tmux is installed and in PATH.")
                return "", "tmux command not found", -1
            except Exception as e:
                logger.error(f"Failed to execute local tmux command: {e}")
                return "", str(e), -1

    def list_sessions(self) -> List[str]:
        """Lists available tmux sessions, locally or remotely."""
        stdout, stderr, return_code = self._execute_tmux_command(["list-sessions", "-F", "#{session_name}"])
        if return_code == 0:
            sessions = stdout.strip().splitlines()
            logger.debug(f"Found sessions: {sessions}")
            return sessions
        elif "no server running" in stderr.lower():
             logger.debug("No tmux server running.")
             return [] # No server means no sessions
        else:
            logger.error(f"Failed to list tmux sessions. Return code: {return_code}, Stderr: {stderr.strip()}")
            # Consider raising an exception or returning empty list based on desired robustness
            return [] # Return empty list on error

    def session_exists(self, name: str) -> bool:
        """Checks if a tmux session with the given name exists."""
        # Using list_sessions is generally reliable. Avoid 'has-session' which can have ambiguous return codes.
        sessions = self.list_sessions()
        exists = name in sessions
        logger.debug(f"Session '{name}' exists: {exists}")
        return exists

    def create_session(self, name: str):
        """Creates a new detached tmux session."""
        logger.info(f"Creating tmux session '{name}'...")
        stdout, stderr, return_code = self._execute_tmux_command(["new-session", "-d", "-s", name])
        if return_code != 0:
            error_message = f"Failed to create tmux session '{name}'. Stderr: {stderr.strip()}"
            logger.error(error_message)
            raise RuntimeError(error_message) # Raise an error on failure
        logger.info(f"Tmux session '{name}' created successfully.")


    def send_command(self, session_name: str, command: str):
        """Sends a command to a specific tmux session."""
        logger.info(f"Sending command to tmux session '{session_name}'...")
        # Ensure the command ends with Enter
        if not command.strip().endswith('\n'):
             command += '\n'
        # Using send-keys. Note: Proper shell escaping within the command itself is the responsibility of the caller.
        stdout, stderr, return_code = self._execute_tmux_command(["send-keys", "-t", session_name, command])
        if return_code != 0:
            error_message = f"Failed to send command to tmux session '{session_name}'. Stderr: {stderr.strip()}"
            logger.error(error_message)
            raise RuntimeError(error_message) # Raise an error on failure
        logger.info(f"Command successfully sent to tmux session '{session_name}'.")

    def kill_session(self, name: str):
        """Kills the specified tmux session."""
        logger.warning(f"Attempting to kill tmux session '{name}'...")
        stdout, stderr, return_code = self._execute_tmux_command(["kill-session", "-t", name])
        if return_code == 0:
            logger.info(f"Successfully killed tmux session '{name}'.")
        else:
            # Check if the error is because the session doesn't exist (which is okay if we intended to overwrite)
            if "can't find session" in stderr.lower() or "no server running" in stderr.lower():
                 logger.warning(f"Session '{name}' did not exist or tmux server not running. No action taken.")
            else:
                error_message = f"Failed to kill tmux session '{name}'. Stderr: {stderr.strip()}"
                logger.error(error_message)
                raise RuntimeError(error_message) # Raise an error on failure
