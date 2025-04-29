import sys
import logging
from pathlib import Path
from appdirs import user_config_dir
from . import PathsManagerInterface
import uuid


class PathsManager(PathsManagerInterface):
    """Manages application paths, handling OS differences."""

    APP_NAME = "hermes_research"
    CONFIG_FILE_NAME = "config.ini"

    def get_absolute_path(self, possibly_relative_path: str) -> str:
        """
        Resolves a possibly relative path to an absolute path.

        Args:
            possibly_relative_path: The path string to resolve.

        Returns:
            The absolute path string.
        """
        return str(Path(possibly_relative_path).resolve())

    def _get_config_root_dir(self) -> Path:
        """
        Determines the root directory for configuration files based on OS.

        - Linux & macOS: Uses ~/.config/hermes_research/
        - Windows: Uses %APPDATA%\\hermes_research\\

        Returns:
            A Path object representing the configuration directory.
        """
        if sys.platform in ["linux", "darwin"]:  # darwin is macOS
            config_dir = Path.home() / ".config" / self.APP_NAME
        elif sys.platform == "win32":
            # Use standard Windows path via appdirs (without appauthor)
            # Gives C:\\Users\\<User>\\AppData\\Roaming\\hermes_research\\
            config_dir = Path(user_config_dir(appname=self.APP_NAME, appauthor=False))
        else:
            # Fallback for other potential OS - default to Unix-like style
            logging.warning(f"Unsupported platform '{sys.platform}'. Defaulting config path to ~/.config/{self.APP_NAME}/")
            config_dir = Path.home() / ".config" / self.APP_NAME

        # Ensure the directory exists
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def get_config_path(self) -> str:
        """
        Gets the full path to the configuration file.

        Returns:
            The absolute path string to the config.ini file.
        """
        config_dir = self._get_config_root_dir()
        return str(config_dir / self.CONFIG_FILE_NAME)

    def get_research_session_path(self, research_parent_directory: str, session_name: str) -> str:
        return str(Path(research_parent_directory) / session_name)

    def get_remote_files_folder(self) -> str:
        """Gets the absolute path for the remote files folder.
        
        Returns:
            A unique path string for remote file transfer in the format:
            /tmp/hermes_research/{uuid4}/
        """
        session_uuid = uuid.uuid4()
        # Construct the path string using f-string formatting
        # Ensure a trailing slash as requested in the format /tmp/hermes_research/{uuid4}/
        path_str = f"/tmp/{self.APP_NAME}/{session_uuid}/"
        # Note: This doesn't create the directory, only returns the path string.
        return path_str
