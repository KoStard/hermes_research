import logging
from argparse import ArgumentParser

# Managers - Interfaces are implicitly used via dependency injection
from hermes_research.utils.paths.paths_manager import PathsManager
from hermes_research.preparation.config.config_manager import ConfigManager
from hermes_research.preparation.menu.hermes_research_menu import HermesResearchMenu
from hermes_research.command.command_manager import HermesResearchCommandManager
from hermes_research.tmux.tmux_manager import TmuxManager
from hermes_research.tmux.ssh.subprocess_ssh_connection import SubprocessSSHConnection
# from hermes_research.remote_copy.scp_remote_copy import SCPRemoteCopy # TASK-002 Placeholder
from hermes_research.preparation.cli.hermes_research_cli import HermesResearchCLI

# Configure logging (Basic setup) - TASK-011
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    # Instantiate dependencies
    paths_manager = PathsManager()
    config_manager = ConfigManager(paths_manager=paths_manager)
    menu = HermesResearchMenu()
    command_manager = HermesResearchCommandManager()
    ssh_connection = SubprocessSSHConnection()
    # remote_copy = SCPRemoteCopy(ssh_connection=ssh_connection) # TASK-002 Placeholder
    tmux_manager = TmuxManager(ssh_connection=ssh_connection) # SSH needed even if not remote initially for interface

    # Instantiate the main CLI class with dependencies
    cli = HermesResearchCLI(
        paths_manager=paths_manager,
        config_manager=config_manager,
        menu=menu,
        command_manager=command_manager,
        tmux_manager=tmux_manager,
        # remote_copy=remote_copy, # TASK-002 Placeholder
        ssh_connection=ssh_connection
    )

    parser = ArgumentParser()
    cli.define_cli(parser)
    args = parser.parse_args()

    try:
        cli.execute(args)
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user.")
        print("\nOperation cancelled.")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
