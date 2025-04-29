import logging
from argparse import ArgumentParser

# Managers - Interfaces are implicitly used via dependency injection
from hermes_research.utils.paths.paths_manager import PathsManager
from hermes_research.preparation.config.config_manager import ConfigManager
from hermes_research.preparation.menu.hermes_research_menu import HermesResearchMenu
from hermes_research.command.command_manager import HermesResearchCommandManager
from hermes_research.tmux.tmux_manager import TmuxManager
from hermes_research.tmux.ssh.subprocess_ssh_connection import SubprocessSSHConnection
from hermes_research.remote_copy.scp_remote_copy import SCPRemoteCopy
from hermes_research.session_name.session_name_manager import SessionNameManager
from hermes_research.preparation.cli.hermes_research_cli import HermesResearchCLI
from hermes_research.preparation.cli.config_cli import ConfigCLI

# Configure logging (Basic setup) - TASK-011
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    # Instantiate dependencies
    paths_manager = PathsManager()
    config_manager = ConfigManager(paths_manager=paths_manager)
    menu = HermesResearchMenu()
    command_manager = HermesResearchCommandManager()
    ssh_connection = SubprocessSSHConnection()
    remote_copy = SCPRemoteCopy(ssh_connection=ssh_connection)
    tmux_manager = TmuxManager(ssh_connection=ssh_connection) # SSH needed even if not remote initially for interface
    session_name_manager = SessionNameManager(tmux_manager=tmux_manager)

    # Instantiate the main CLI class with dependencies
    research_cli = HermesResearchCLI(
        paths_manager=paths_manager,
        config_manager=config_manager,
        menu=menu,
        command_manager=command_manager,
        tmux_manager=tmux_manager,
        remote_copy=remote_copy,
        ssh_connection=ssh_connection,
        session_name_manager=session_name_manager
    )
    
    # Instantiate the config CLI class
    config_cli = ConfigCLI(
        config_manager=config_manager,
        paths_manager=paths_manager
    )

    # Create main parser
    parser = ArgumentParser(
        prog="hermes-research",
        description="Hermes Research - A tool for managing AI research sessions"
    )
    
    # Create subparsers for different command groups
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Add the "research" command (default behavior)
    research_parser = subparsers.add_parser(
        "research", 
        help="Start a research session (default command)"
    )
    research_cli.define_cli(research_parser)
    
    # Add the "config" command and its subcommands
    config_cli.define_cli(subparsers)
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        # Handle different command groups
        if not args.command or args.command == "research":
            research_cli.execute(args)
        elif args.command == "config":
            config_cli.execute(args)
        else:
            logger.error(f"Unknown command: {args.command}")
            parser.print_help()
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user.")
        logger.info("\nOperation cancelled.")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        logger.error(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()
