import logging
import os
import subprocess
from typing import Dict

from ..remote_copy import RemoteCopyInterface
from ..tmux.ssh import SSHConnectionInterface, SSHDestination
from ..tmux.ssh.subprocess_ssh_connection import SSHCommandError, SSHTimeoutError

logger = logging.getLogger(__name__)

class SCPRemoteCopy(RemoteCopyInterface):
    """Implements RemoteCopyInterface using SCP to copy files to a remote server."""
    
    def __init__(self, ssh_connection: SSHConnectionInterface, timeout: int = 60):
        """
        Initialize with an SSH connection handler.
        
        Args:
            ssh_connection: SSH connection interface for remote command execution
            timeout: Timeout in seconds for SCP operations (default: 60)
        """
        self.ssh_connection = ssh_connection
        self.timeout = timeout
        
    def remote_copy_files(self, source_to_target_paths_map: Dict[str, str], destination: SSHDestination) -> None:
        """
        Copy files from local paths to specified remote paths using SCP.
        
        Args:
            source_to_target_paths_map: Dictionary mapping local source paths to remote target paths
            destination: The SSH destination details
            
        Raises:
            FileNotFoundError: If a source file doesn't exist or scp is not found
            SSHCommandError: If SCP command fails
            SSHTimeoutError: If SCP operation times out
        """
        # First, ensure all source files exist
        for source_path in source_to_target_paths_map.keys():
            if not os.path.isfile(source_path):
                msg = f"Source file not found: {source_path}"
                logger.error(msg)
                raise FileNotFoundError(msg)
        
        # Group files by target directories to optimize directory creation
        target_dirs = set()
        for target_path in source_to_target_paths_map.values():
            target_dir = os.path.dirname(target_path)
            if target_dir:
                target_dirs.add(target_dir)
        
        # Create all required remote directories
        for remote_dir in sorted(target_dirs):
            try:
                mkdir_command = f"mkdir -p {remote_dir}"
                stdout, stderr, return_code = self.ssh_connection.execute_command_on_remote(
                    mkdir_command, destination
                )
                
                if return_code != 0:
                    msg = f"Failed to create remote directory {remote_dir}: {stderr}"
                    logger.error(msg)
                    raise SSHCommandError(msg)
                    
                logger.debug(f"Created remote directory: {remote_dir}")
            except Exception as e:
                msg = f"Error creating remote directory {remote_dir}: {str(e)}"
                logger.error(msg)
                raise SSHCommandError(msg) from e
        
        # Copy each file using scp
        for source_path, target_path in source_to_target_paths_map.items():
            try:
                logger.info(f"Copying {source_path} to {destination.username}@{destination.hostname}:{target_path}")
                
                # Build and execute scp command
                scp_command = ["scp", source_path, f"{destination.username}@{destination.hostname}:{target_path}"]
                logger.debug(f"Running SCP command: {' '.join(scp_command)}")
                
                result = subprocess.run(
                    scp_command,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
                
                if result.returncode != 0:
                    msg = f"SCP command failed for {source_path}: {result.stderr}"
                    logger.error(msg)
                    raise SSHCommandError(msg)
                    
                logger.debug(f"Successfully copied {source_path} to remote")
                
            except FileNotFoundError:
                msg = "SCP command not found. Please ensure OpenSSH client is installed and in PATH."
                logger.error(msg)
                raise FileNotFoundError(msg)
                
            except subprocess.TimeoutExpired:
                msg = f"SCP operation timed out while copying {source_path}"
                logger.error(msg)
                raise SSHTimeoutError(msg)
                
            except Exception as e:
                msg = f"Error during file transfer of {source_path}: {str(e)}"
                logger.error(msg)
                raise SSHCommandError(msg) from e
