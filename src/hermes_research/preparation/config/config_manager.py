import configparser
import json
import os
from typing import Dict, List

from hermes_research.preparation.config import (
    ConfigManagerInterface,
    HermesConfig,
    HermesConfigRemoteServer,
)
from hermes_research.utils.paths import PathsManagerInterface


class ConfigManager(ConfigManagerInterface):
    """Manages application configuration using an INI file."""

    def __init__(self, paths_manager: PathsManagerInterface):
        """
        Initializes the ConfigManager.

        Args:
            paths_manager: An instance of PathsManagerInterface to get the config path.
        """
        self.paths_manager = paths_manager
        self.config_path = self.paths_manager.get_config_path()
        # Ensure config exists on initialization, creating a default one if necessary
        if not os.path.exists(self.config_path):
            self.initialize_default_config()

    def _get_config_parser(self) -> configparser.ConfigParser:
        """Reads the config file and returns a ConfigParser object."""
        parser = configparser.ConfigParser()
        # Prevent ConfigParser from lowercasing keys
        parser.optionxform = str 
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")
        parser.read(self.config_path)
        return parser

    def _save_parser(self, parser: configparser.ConfigParser):
        """Saves the ConfigParser object to the config file."""
        # Ensure the directory exists
        config_dir = os.path.dirname(self.config_path)
        if config_dir: # Ensure config_dir is not empty (e.g., if path is just a filename)
             os.makedirs(config_dir, exist_ok=True)
        with open(self.config_path, 'w') as configfile:
            parser.write(configfile)

    def load_config(self) -> HermesConfig:
        """Loads the configuration from the INI file."""
        try:
            parser = self._get_config_parser()
        except FileNotFoundError:
            # If file not found after initial check (e.g., deleted externally), re-initialize
            self.initialize_default_config()
            parser = self._get_config_parser()


        # Load general settings
        research_directory = parser.get('general', 'research_directory', fallback='')
        default_budget_str = parser.get('general', 'default_budget', fallback='30')
        try:
            default_budget = int(default_budget_str)
        except ValueError:
            default_budget = 30 # Fallback to default if conversion fails
            
        models_str = parser.get('general', 'models', fallback='')
        models = [model.strip() for model in models_str.split(',') if model.strip()] if models_str else []

        # Load remote servers
        remote_servers: Dict[str, HermesConfigRemoteServer] = {}
        if parser.has_section('remote_servers'):
            for name, value in parser.items('remote_servers'):
                try:
                    server_data = json.loads(value)
                    remote_servers[name] = HermesConfigRemoteServer(**server_data)
                except (json.JSONDecodeError, TypeError) as e:
                    # Handle potential errors if the JSON is malformed or doesn't match dataclass
                    print(f"Warning: Could not parse remote server '{name}'. Error: {e}")
                    continue # Skip this server

        return HermesConfig(
            research_directory=research_directory,
            default_budget=default_budget,
            remote_servers=remote_servers,
            models=models
        )

    def _save_config(self, config: HermesConfig):
        """Saves the HermesConfig object to the INI file."""
        parser = configparser.ConfigParser()
        # Prevent ConfigParser from lowercasing keys
        parser.optionxform = str

        # General section
        parser['general'] = {
            'research_directory': config.research_directory,
            'models': ','.join(config.models),
            'default_budget': str(config.default_budget)
        }

        # Remote servers section
        parser['remote_servers'] = {}
        for name, server_config in config.remote_servers.items():
            # Convert dataclass to dict then to JSON string
            server_data = {
                "hostname": server_config.hostname,
                "username": server_config.username,
                "remote_research_path": server_config.remote_research_path
            }
            parser['remote_servers'][name] = json.dumps(server_data)

        self._save_parser(parser)

    def add_model(self, model_name: str) -> None:
        """Adds a model name to the configuration."""
        config = self.load_config()
        if model_name not in config.models:
            config.models.append(model_name)
            self._save_config(config)

    def remove_model(self, model_name: str) -> None:
        """Removes a model name from the configuration."""
        config = self.load_config()
        if model_name in config.models:
            config.models.remove(model_name)
            self._save_config(config)

    def set_research_directory(self, research_directory: str) -> None:
        """Sets the research directory path in the configuration."""
        config = self.load_config()
        config.research_directory = research_directory
        self._save_config(config)

    def set_default_budget(self, budget: int) -> None:
        """Sets the default budget in the configuration."""
        config = self.load_config()
        config.default_budget = budget
        self._save_config(config)

    def add_remote_server(self, name: str, hostname: str, username: str, remote_research_path: str) -> None:
        """Adds or updates a remote server configuration."""
        config = self.load_config()
        server_config = HermesConfigRemoteServer(
            hostname=hostname,
            username=username,
            remote_research_path=remote_research_path
        )
        config.remote_servers[name] = server_config
        self._save_config(config)

    def remove_remote_server(self, name: str) -> None:
        """Removes a remote server configuration by name."""
        config = self.load_config()
        if name in config.remote_servers:
            del config.remote_servers[name]
            self._save_config(config)

    def initialize_default_config(self):
        """Initializes and saves a default configuration file."""
        print(f"Initializing default configuration at {self.config_path}")
        default_config = HermesConfig(
            research_directory="",
            models=[],
            default_budget=30,
            remote_servers={}
        )
        self._save_config(default_config)
