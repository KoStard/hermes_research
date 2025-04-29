import logging
from argparse import ArgumentParser, _SubParsersAction

from hermes_research.preparation.cli import ConfigCLIInterface
from hermes_research.preparation.config import ConfigManagerInterface
from hermes_research.utils.paths import PathsManagerInterface

logger = logging.getLogger(__name__)


class ConfigCLI(ConfigCLIInterface):
    """CLI for managing Hermes Research configuration."""

    def __init__(self, config_manager: ConfigManagerInterface, paths_manager: PathsManagerInterface):
        """Initialize with config manager and paths manager.
        
        Args:
            config_manager: Manager for config operations
            paths_manager: Manager for path operations
        """
        self.config_manager = config_manager
        self.paths_manager = paths_manager
        logger.debug("ConfigCLI initialized with dependencies.")

    def define_cli(self, subparsers: _SubParsersAction):
        """Define configuration subcommands."""
        # Create a parser for the "config" command
        config_parser = subparsers.add_parser(
            "config", 
            help="Manage Hermes Research configuration"
        )
        
        # Create subcommands for the config parser
        config_subparsers = config_parser.add_subparsers(
            dest="config_command",
            help="Configuration commands"
        )
        
        # Show config command
        show_parser = config_subparsers.add_parser(
            "show", 
            help="Show current configuration"
        )
        
        # Set research directory command
        dir_parser = config_subparsers.add_parser(
            "set-research-dir", 
            help="Set the research directory"
        )
        dir_parser.add_argument(
            "path", 
            help="Path to the research directory"
        )
        
        # Set default budget command
        budget_parser = config_subparsers.add_parser(
            "set-default-budget", 
            help="Set the default budget"
        )
        budget_parser.add_argument(
            "budget", 
            type=int, 
            help="Default budget value"
        )
        
        # Model management commands
        model_parser = config_subparsers.add_parser(
            "model", 
            help="Manage model configurations"
        )
        model_subparsers = model_parser.add_subparsers(
            dest="model_command",
            help="Model management commands"
        )
        
        # Add model command
        add_model_parser = model_subparsers.add_parser(
            "add", 
            help="Add a model"
        )
        add_model_parser.add_argument(
            "name", 
            help="Model name"
        )
        
        # Remove model command
        remove_model_parser = model_subparsers.add_parser(
            "remove", 
            help="Remove a model"
        )
        remove_model_parser.add_argument(
            "name", 
            help="Model name"
        )
        
        # List models command
        list_models_parser = model_subparsers.add_parser(
            "list", 
            help="List configured models"
        )
        
        # Server management commands
        server_parser = config_subparsers.add_parser(
            "server", 
            help="Manage remote server configurations"
        )
        server_subparsers = server_parser.add_subparsers(
            dest="server_command",
            help="Server management commands"
        )
        
        # Add server command
        add_server_parser = server_subparsers.add_parser(
            "add", 
            help="Add or update a remote server"
        )
        add_server_parser.add_argument(
            "name", 
            help="Server name"
        )
        add_server_parser.add_argument(
            "hostname", 
            help="Server hostname"
        )
        add_server_parser.add_argument(
            "username", 
            help="SSH username"
        )
        add_server_parser.add_argument(
            "remote_research_path", 
            help="Remote research directory path"
        )
        
        # Remove server command
        remove_server_parser = server_subparsers.add_parser(
            "remove", 
            help="Remove a remote server"
        )
        remove_server_parser.add_argument(
            "name", 
            help="Server name"
        )
        
        # List servers command
        list_servers_parser = server_subparsers.add_parser(
            "list", 
            help="List configured servers"
        )

    def execute(self, args):
        """Execute the config command based on parsed arguments."""
        if not hasattr(args, "config_command"):
            logger.error("No configuration command specified")
            return
            
        if args.config_command == "show":
            self._show_config()
        elif args.config_command == "set-research-dir":
            self._set_research_dir(args.path)
        elif args.config_command == "set-default-budget":
            self._set_default_budget(args.budget)
        elif args.config_command == "model":
            self._handle_model_command(args)
        elif args.config_command == "server":
            self._handle_server_command(args)
        else:
            logger.error(f"Unknown configuration command: {args.config_command}")
    
    def _show_config(self):
        """Show the current configuration."""
        config = self.config_manager.load_config()
        logger.info("Current Configuration:")
        logger.info(f"  Config file: {self.paths_manager.get_config_path()}")
        logger.info(f"  Research directory: {config.research_directory or '(not set)'}")
        logger.info(f"  Default budget: {config.default_budget}")
        
        # Show models
        if config.models:
            logger.info("  Models:")
            for model in config.models:
                logger.info(f"    - {model}")
        else:
            logger.info("  Models: (none configured)")
        
        # Show remote servers
        if config.remote_servers:
            logger.info("  Remote servers:")
            for name, server in config.remote_servers.items():
                logger.info(f"    - {name}:")
                logger.info(f"        Hostname: {server.hostname}")
                logger.info(f"        Username: {server.username}")
                logger.info(f"        Remote research path: {server.remote_research_path}")
        else:
            logger.info("  Remote servers: (none configured)")
    
    def _set_research_dir(self, path):
        """Set the research directory."""
        abs_path = self.paths_manager.get_absolute_path(path)
        self.config_manager.set_research_directory(abs_path)
        logger.info(f"Research directory set to: {abs_path}")
    
    def _set_default_budget(self, budget):
        """Set the default budget."""
        if budget <= 0:
            logger.error("Budget must be a positive integer")
            return
        
        self.config_manager.set_default_budget(budget)
        logger.info(f"Default budget set to: {budget}")
    
    def _handle_model_command(self, args):
        """Handle model-related commands."""
        if not hasattr(args, "model_command") or not args.model_command:
            logger.error("No model command specified")
            return
            
        if args.model_command == "add":
            self._add_model(args.name)
        elif args.model_command == "remove":
            self._remove_model(args.name)
        elif args.model_command == "list":
            self._list_models()
        else:
            logger.error(f"Unknown model command: {args.model_command}")
    
    def _add_model(self, name):
        """Add a model to the configuration."""
        self.config_manager.add_model(name)
        logger.info(f"Added model: {name}")
    
    def _remove_model(self, name):
        """Remove a model from the configuration."""
        config = self.config_manager.load_config()
        if name not in config.models:
            logger.error(f"Model '{name}' not found in configuration")
            return
            
        self.config_manager.remove_model(name)
        logger.info(f"Removed model: {name}")
    
    def _list_models(self):
        """List configured models."""
        config = self.config_manager.load_config()
        if not config.models:
            logger.info("No models configured")
            return
            
        logger.info("Configured models:")
        for model in config.models:
            logger.info(f"  - {model}")
    
    def _handle_server_command(self, args):
        """Handle server-related commands."""
        if not hasattr(args, "server_command") or not args.server_command:
            logger.error("No server command specified")
            return
            
        if args.server_command == "add":
            self._add_server(args.name, args.hostname, args.username, args.remote_research_path)
        elif args.server_command == "remove":
            self._remove_server(args.name)
        elif args.server_command == "list":
            self._list_servers()
        else:
            logger.error(f"Unknown server command: {args.server_command}")
    
    def _add_server(self, name, hostname, username, remote_research_path):
        """Add or update a remote server configuration."""
        self.config_manager.add_remote_server(
            name=name,
            hostname=hostname,
            username=username,
            remote_research_path=remote_research_path
        )
        logger.info(f"Added/updated server '{name}'")
    
    def _remove_server(self, name):
        """Remove a remote server configuration."""
        config = self.config_manager.load_config()
        if name not in config.remote_servers:
            logger.error(f"Server '{name}' not found in configuration")
            return
            
        self.config_manager.remove_remote_server(name)
        logger.info(f"Removed server: {name}")
    
    def _list_servers(self):
        """List configured remote servers."""
        config = self.config_manager.load_config()
        if not config.remote_servers:
            logger.info("No remote servers configured")
            return
            
        logger.info("Configured remote servers:")
        for name, server in config.remote_servers.items():
            logger.info(f"  - {name}:")
            logger.info(f"      Hostname: {server.hostname}")
            logger.info(f"      Username: {server.username}")
            logger.info(f"      Remote research path: {server.remote_research_path}")
