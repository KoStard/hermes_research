from abc import ABC, abstractmethod

class PathsManagerInterface(ABC):
    @abstractmethod
    def get_absolute_path(self, possibly_relative_path: str) -> str:
        pass
    
    @abstractmethod
    def get_config_path(self) -> str:
        pass

    @abstractmethod
    def get_research_session_path(self, research_parent_directory: str, session_name: str) -> str:
        """Gets the absolute path for a specific research session directory."""
        pass

    @abstractmethod
    def get_remote_files_folder(self) -> str:
        """Gets the absolute path for the remote files folder."""
        pass
