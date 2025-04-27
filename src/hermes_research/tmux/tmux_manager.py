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
    """Manages tmux sessions locally or remotely via SSH."""

    def __init__(self, ssh_connection: SSHConnectionInterface):
        self._ssh_connection = ssh_connection
        self._remote_destination: Optional[SSHDestination] = None
        logger.info("TmuxManager initialized.")

    def set_remote(self, destination: SSHDestination):
        """
        Set the SSH destination for remote tmux operations.
        If not set, operations run locally.
        """
        self._remote_destination = destination
        logger.info(f"TmuxManager remote destination set to: {destination}")

    def _execute_command(self, command_args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Executes a command locally or remotely via SSH."""
        full_command = shlex.join(command_args)
        logger.debug(f"Executing command: {full_command}")

        if self._remote_destination:
            # For remote execution, unset TMUX env var locally before calling SSH
            # Prefix the remote command to unset TMUX, handling potential nested sessions.
            remote_command = f"unset TMUX; {full_command}"
            logger.debug(f"Executing remote command via SSH: {remote_command}")
            try:
                # Execute the command remotely and get stdout, stderr, and return code
                stdout, stderr, return_code = self._ssh_connection.execute_command_on_remote(
                    remote_command, self._remote_destination
                )
                logger.debug(f"Remote command result: {return_code}, stdout: {stdout.strip()}, stderr: {stderr.strip()}")

                # Create a CompletedProcess object for consistency
                result = subprocess.CompletedProcess(
                    args=command_args,
                    returncode=return_code,
                    stdout=stdout,
                    stderr=stderr,
                )

                # If check is True and the command failed, raise CalledProcessError
                if check and result.returncode != 0:
                    raise subprocess.CalledProcessError(
                        returncode=result.returncode,
                        cmd=result.args,
                        output=result.stdout,
                        stderr=result.stderr,
                    )
                return result
            except Exception as e:
                # Catch potential exceptions from the SSH layer itself or re-raise CalledProcessError
                logger.error(f"Remote command execution failed: {e}")
                if check and not isinstance(e, subprocess.CalledProcessError):
                     # If check is True and it wasn't a CalledProcessError already raised, wrap the exception
                     raise RuntimeError(f"SSH command execution failed: {e}") from e
                elif isinstance(e, subprocess.CalledProcessError):
                     # If it was already a CalledProcessError, just re-raise if check=True
                     if check:
                         raise
                     else:
                         # If check=False, return the exception object containing details
                         return e
                else:
                    # If check=False and it was another exception (not CalledProcessError),
                    # return a CompletedProcess indicating failure.
                    return subprocess.CompletedProcess(command_args, returncode=1, stdout="", stderr=str(e))

        else:
            # For local execution, use the context manager
            with _UnsetTmuxEnv():
                try:
                    result = subprocess.run(command_args, capture_output=True, text=True, check=check)
                    logger.debug(f"Local command result: {result.returncode}, stdout: {result.stdout.strip()}, stderr: {result.stderr.strip()}")
                    return result
                except FileNotFoundError:
                    logger.error("tmux command not found. Please ensure tmux is installed and in PATH.")
                    raise
                except subprocess.CalledProcessError as e:
                    logger.error(f"Local command failed: {e.stderr}")
                    if check:
                        raise
                    # If check=False, return the exception object which contains details
                    return e

    def list_sessions(self) -> List[str]:
        """Lists active tmux sessions."""
        command = ["tmux", "list-sessions", "-F", "#{session_name}"]
        try:
            result = self._execute_command(command, check=True)
            sessions = result.stdout.strip().splitlines()
            logger.info(f"Found tmux sessions: {sessions}")
            return sessions
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            # If tmux isn't running or list-sessions fails (e.g., no server), return empty list
            logger.warning(f"Could not list tmux sessions (maybe server not running?): {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred while listing sessions: {e}")
            return []


    def create_session(self, name: str):
        """Creates a new detached tmux session."""
        command = ["tmux", "new-session", "-d", "-s", name]
        try:
            self._execute_command(command, check=True)
            logger.info(f"Successfully created tmux session: {name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create tmux session '{name}': {e.stderr}")
            raise RuntimeError(f"Failed to create tmux session '{name}': {e.stderr}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during session creation: {e}")
            raise


    def send_command(self, session_name: str, command: str):
        """Sends a command to a specific tmux session."""
        # Ensure the command is treated as a single argument, even with spaces
        tmux_command = ["tmux", "send-keys", "-t", session_name, command, "Enter"]
        try:
            self._execute_command(tmux_command, check=True)
            logger.info(f"Successfully sent command to session '{session_name}': {command}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to send command to session '{session_name}': {e.stderr}")
            raise RuntimeError(f"Failed to send command to session '{session_name}': {e.stderr}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred while sending command: {e}")
            raise

    def determine_alternative_name(self, rejected_session_name: str) -> str:
        """Determines an alternative session name if the initial one is taken."""
        existing_sessions = self.list_sessions()
        base_name = rejected_session_name
        counter = 1
        new_name = f"{base_name}-{counter}"
        while new_name in existing_sessions:
            counter += 1
            new_name = f"{base_name}-{counter}"
            if counter > 100: # Safety break
                 logger.error(f"Could not find an alternative name for {rejected_session_name} after 100 attempts.")
                 raise RuntimeError(f"Could not determine an alternative session name for {rejected_session_name}")
        logger.info(f"Determined alternative session name: {new_name}")
        return new_name
