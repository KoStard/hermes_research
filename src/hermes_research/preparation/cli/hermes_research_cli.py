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
        # remote_copy: RemoteCopyInterface, # TASK-002 Placeholder
        ssh_connection: SSHConnectionInterface, # TASK-006 Placeholder for remote flow
        session_name_manager: SessionNameManagerInterface
    ):
        self.paths_manager = paths_manager
        self.config_manager = config_manager
        self.menu = menu
        self.command_manager = command_manager
        self.tmux_manager = tmux_manager
        # self.remote_copy = remote_copy # TASK-002 Placeholder
        self.ssh_connection = ssh_connection # TASK-006 Placeholder for remote flow
        self.session_name_manager = session_name_manager
        logger.debug("HermesResearchCLI initialized with dependencies.")

    def define_cli(self, parser: ArgumentParser):
        parser.add_argument("files", help="Path to the files to be included", nargs="*")
        # TASK-009: Add -c argument
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

        # Set config for menu and get user selections
        self.menu.set_config(config)
        selection = self.menu.get_selection() # Can raise KeyboardInterrupt or other exceptions

        session_name = selection.session_name
        extra_args = args.command_args

        # Resolve input file paths to absolute paths (TASK-005)
        absolute_file_paths = [self.paths_manager.get_absolute_path(f) for f in args.files]
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

            # TODO: TASK-014 - Create temporary command script in /tmp
            # Left empty for now after reverting TASK-012 implementation

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
                # Send the command string directly
                self.tmux_manager.send_command(session_name, hermes_command)

                # Use logger.info for all user-facing messages
                logger.info(f"\nLocal research session '{session_name}' started in tmux.")
                logger.info(f"You can attach to it using: tmux attach -t {session_name}")

            except Exception as e:
                logger.error(f"Failed to start local tmux session: {e}")
                logger.error(f"\nError starting tmux session: {e}")
                # Attempt cleanup? The session might exist partially. Difficult to handle perfectly here.

        else:
            # --- Remote Execution Flow (Placeholder for Phase 2) ---
            logger.info(f"Preparing remote research session '{session_name}' on server '{selection.selected_server_name}'...")
            logger.info("\nRemote execution is not yet implemented in Phase 1.")
            # TODO: Implement Phase 2 logic here based on docs/cli_implementation_plan.md
            # 1. Get Remote Config
            # 2. Define Final Remote Research Path
            # 3. Define Remote Temp Path
            # 4. Create Remote Temp Dir (SSH)
            # 5. Generate Remote Command (using temp paths for files, final path for --deep-research)
            # 6. Create Local Temp Script
            # 7. Prepare File Map
            # 8. Copy Files (RemoteCopy)
            # 9. Configure Tmux for Remote
            remote_config = config.remote_servers.get(selection.selected_server_name)
            if remote_config:
                # Create SSH destination from config
                ssh_destination = SSHDestination(
                    username=remote_config.username,
                    hostname=remote_config.hostname
                )
                self.tmux_manager.set_remote(ssh_destination)
                
                # 10. Manage Remote Tmux Session (check exists, create, send command - execute script)
                try:
                    session_name = self.session_name_manager.handle_session_name_conflict(
                        session_name, 
                        is_remote=True,
                        server_name=selection.selected_server_name
                    )
                except KeyboardInterrupt:
                    logger.info("Operation cancelled.")
                    # TODO: Cleanup any temporary files created for remote execution
                    return
                
                # Continue with remote command execution...
                logger.info("Remote tmux session handling implemented, but full remote execution not yet available.")
            else:
                logger.error(f"Remote server '{selection.selected_server_name}' configuration not found.")
                return
            
            # 11. Cleanup Local Temp Script
            pass
