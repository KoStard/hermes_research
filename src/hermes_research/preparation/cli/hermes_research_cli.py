import logging
import os
from argparse import ArgumentParser, Namespace

# Interfaces
from hermes_research.preparation.cli import HermesResearchCLIInterface
from hermes_research.utils.paths import PathsManagerInterface
from hermes_research.preparation.config import ConfigManagerInterface
from hermes_research.preparation.menu import HermesResearchMenuInterface, MenuSelection
from hermes_research.command import HermesResearchCommandManagerInterface
from hermes_research.tmux import TmuxManagerInterface
from hermes_research.remote_copy import RemoteCopyInterface # Needed for constructor signature
from hermes_research.tmux.ssh import SSHConnectionInterface, SSHDestination # Needed for constructor signature
from hermes_research.session_name import SessionNameManagerInterface

# Concrete classes / helpers
from hermes_research.preparation.menu.menu_manager import MenuManager # For prompts

logger = logging.getLogger(__name__)


class HermesResearchCLI(HermesResearchCLIInterface):
    def __init__(
        self,
        paths_manager: PathsManagerInterface,
        config_manager: ConfigManagerInterface,
        menu: HermesResearchMenuInterface,
        command_manager: HermesResearchCommandManagerInterface,
        tmux_manager: TmuxManagerInterface,
        remote_copy: RemoteCopyInterface,
        ssh_connection: SSHConnectionInterface,
        session_name_manager: SessionNameManagerInterface
    ):
        self.paths_manager = paths_manager
        self.config_manager = config_manager
        self.menu = menu
        self.command_manager = command_manager
        self.tmux_manager = tmux_manager
        self.remote_copy = remote_copy
        self.ssh_connection = ssh_connection # TASK-006 Placeholder for remote flow
        self.session_name_manager = session_name_manager
        logger.debug("HermesResearchCLI initialized with dependencies.")

    def define_cli(self, parser: ArgumentParser):
        parser.add_argument("files", help="Path to the files to be included", nargs="*")
        parser.add_argument(
            "-c", "--command-args",
            help="Additional arguments to pass directly to the hermes command, enclosed in quotes.",
            type=str,
            default=""
        )


    def execute(self, args: Namespace):
        """Orchestrates the research task setup and execution."""
        logger.info("Starting Hermes Research CLI...")

        # Load configuration
        config = self.config_manager.load_config()
        if not config.research_directory:
             logger.error("Research directory is not set in the configuration.")
             # TODO: Add command to configure settings later
             return # Exit if essential config is missing
        
        extra_args = args.command_args
        files = args.files

        # Set config for menu and get user selections
        self.menu.set_config(config)
        selection = self.menu.get_selection() # Can raise KeyboardInterrupt or other exceptions

        session_name = selection.session_name

        # Resolve input file paths to absolute paths (TASK-005)
        absolute_file_paths = [self.paths_manager.get_absolute_path(f) for f in files]
        logger.debug(f"Absolute input file paths: {absolute_file_paths}")

        # --- Execution Flow ---
        if selection.selected_server_name is None:
            # --- Local Execution Flow (Phase 1 Implementation) ---
            logger.info(f"Starting local research session '{session_name}'...")

            # Get local session path (TASK-005)
            local_session_path = self.paths_manager.get_research_session_path(
                research_parent_directory=config.research_directory,
                session_name=session_name
            )
            logger.debug(f"Local session path: {local_session_path}")

            # Generate command (TASK-005 - using absolute paths)
            hermes_command = self.command_manager.generate_command(
                path_to_research=local_session_path, # Use session path for --deep-research
                model=selection.model,
                files=absolute_file_paths, # Pass absolute paths
                budget=selection.budget,
                prompt=selection.prompt,
                extra_arguments=extra_args # Pass extra args (TASK-009)
            )
            logger.debug(f"Generated Hermes command:\n{hermes_command}")

            # Create temporary command script in /tmp (TASK-014)
            temp_script_path = self.command_manager.create_temp_script(hermes_command)
            logger.debug(f"Created temporary script at: {temp_script_path}")

            # Manage Tmux Session (TASK-010)
            self.tmux_manager.set_remote(None) # Ensure local mode
            try:
                session_name = self.session_name_manager.handle_session_name_conflict(session_name, is_remote=False)
            except KeyboardInterrupt:
                logger.info("Operation cancelled.")
                return

            try:
                logger.info(f"Creating tmux session '{session_name}'...") # TASK-011 Feedback
                self.tmux_manager.create_session(session_name)

                logger.info("Sending command to tmux session...") # TASK-011 Feedback
                # Source the temporary script in the tmux session
                self.tmux_manager.send_command(session_name, f". {temp_script_path}")

                # Use logger.info for all user-facing messages
                logger.info(f"\nLocal research session '{session_name}' started in tmux.")
                logger.info(f"You can attach to it using: tmux attach -t {session_name}")

            except Exception as e:
                logger.error(f"Failed to start local tmux session: {e}")
                logger.error(f"\nError starting tmux session: {e}")
                # Attempt cleanup? The session might exist partially. Difficult to handle perfectly here.

        else:
            # --- Remote Execution Flow ---
            logger.info(f"Preparing remote research session '{session_name}' on server '{selection.selected_server_name}'...")
            
            # 1. Get Remote Config
            remote_config = config.remote_servers.get(selection.selected_server_name)
            if not remote_config:
                logger.error(f"Remote server '{selection.selected_server_name}' configuration not found.")
                return
            
            # Create SSH destination from config
            ssh_destination = SSHDestination(
                username=remote_config.username,
                hostname=remote_config.hostname
            )
            
            # 2. Define Final Remote Research Path
            remote_research_path = os.path.join(
                remote_config.remote_research_path,
                session_name
            )
            logger.debug(f"Remote research path: {remote_research_path}")
            
            # 3. Define Remote Temp Path
            remote_temp_dir = self.paths_manager.get_remote_files_folder()
            logger.debug(f"Remote temporary directory: {remote_temp_dir}")
            
            # Initialize remote file paths list before using it
            remote_file_paths = []
            
            # 5. Generate Remote Command with remote file paths
            logger.info("Generating remote command script...")
            hermes_command = self.command_manager.generate_command(
                path_to_research=remote_research_path,  # Use remote path for --deep-research
                model=selection.model,
                files=remote_file_paths,  # Use remote paths for files
                budget=selection.budget,
                prompt=selection.prompt,
                extra_arguments=extra_args
            )
            logger.debug(f"Generated remote Hermes command:\n{hermes_command}")
            
            # 6. Create Local Temp Script
            temp_script_path = self.command_manager.create_temp_script(hermes_command)
            logger.debug(f"Created temporary script at: {temp_script_path}")
            
            try:
                # Test SSH connection
                logger.info(f"Testing SSH connection to {remote_config.username}@{remote_config.hostname}...")
                if not self.ssh_connection.test_connection(ssh_destination):
                    logger.error(f"SSH connection to {remote_config.username}@{remote_config.hostname} failed.")
                    return
                
                # 4. Create Remote Temp Dir (SSH)
                logger.info(f"Creating remote temporary directory on {remote_config.hostname}:{remote_temp_dir}...")
                mkdir_cmd = f"mkdir -p {remote_temp_dir}"
                stdout, stderr, returncode = self.ssh_connection.execute_command_on_remote(
                    mkdir_cmd, ssh_destination
                )
                if returncode != 0:
                    logger.error(f"Failed to create remote temporary directory: {stderr}")
                    return
                
                # 7 & 8. Prepare File Map and Copy Files
                source_to_target_paths_map = {}
                remote_file_paths = []  # Track remote paths for command generation
            
                # Map original files
                for file_path in absolute_file_paths:
                    file_name = os.path.basename(file_path)
                    remote_file_path = os.path.join(remote_temp_dir, file_name)
                    source_to_target_paths_map[file_path] = remote_file_path
                    remote_file_paths.append(remote_file_path)
                    logger.debug(f"Mapping: {file_path} -> {remote_file_path}")
            
                # Add script to map
                remote_script_path = os.path.join(remote_temp_dir, "run_research.sh")
                source_to_target_paths_map[temp_script_path] = remote_script_path
                logger.debug(f"Mapping script: {temp_script_path} -> {remote_script_path}")
            
                # Execute copy operation
                logger.info(f"Copying files to {remote_config.hostname}...")
                try:
                    self.remote_copy.remote_copy_files(source_to_target_paths_map, ssh_destination)
                    logger.info("All files copied successfully.")
                except Exception as e:
                    logger.error(f"Failed to copy files to remote server: {e}")
                    return  # Exit if file copying fails
                
                # 9. Configure Tmux for Remote
                logger.info(f"Configuring tmux for remote server '{selection.selected_server_name}'...")
                self.tmux_manager.set_remote(ssh_destination)
                
                # 10. Manage Remote Tmux Session
                try:
                    session_name = self.session_name_manager.handle_session_name_conflict(
                        session_name, 
                        is_remote=True,
                        server_name=selection.selected_server_name
                    )
                except KeyboardInterrupt:
                    logger.info("Operation cancelled.")
                    # Cleanup any temporary files created for remote execution
                    return
                
                # Create remote tmux session
                logger.info(f"Creating remote tmux session '{session_name}' on {remote_config.hostname}...")
                self.tmux_manager.create_session(session_name)
                
                # Send command to remote tmux session
                logger.info("Sending command to remote tmux session...")
                # Execute the remote script
                logger.info(f"Executing script on {remote_config.hostname}...")
                self.tmux_manager.send_command(session_name, f". {remote_script_path}")
                
                # Success message with connection instructions
                logger.info(f"Remote research session '{session_name}' started on '{remote_config.hostname}'.")
                logger.info(f"You can attach to it using: ssh {remote_config.username}@{remote_config.hostname} \"tmux attach -t {session_name}\"")
                
            except Exception as e:
                logger.error(f"An error occurred during remote execution: {e}")
                # Cleanup remote temporary directory (optional - leaving for debugging)
                # The following lines could be uncommented to clean up remote temp dir
                # logger.debug(f"Cleaning up remote temporary directory: {remote_temp_dir}")
                # cleanup_cmd = f"rm -rf {remote_temp_dir}"
                # self.ssh_connection.execute_command_on_remote(cleanup_cmd, ssh_destination)
                return
            finally:
                # 11. Cleanup Local Temp Script
                if os.path.exists(temp_script_path):
                    logger.debug(f"Cleaning up local temporary script: {temp_script_path}")
                    # Clean up the local temporary script
                    try:
                        if os.path.exists(temp_script_path):
                            os.unlink(temp_script_path)
                            logger.debug(f"Removed local temporary script: {temp_script_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove temporary script {temp_script_path}: {e}")
