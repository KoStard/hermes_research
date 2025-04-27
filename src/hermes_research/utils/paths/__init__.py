from abc import ABC, abstractmethod

class PathsManagerInterface(ABC):
    @abstractmethod
    def get_absolute_path(self, possibly_relative_path: str) -> str:
        pass
    
    @abstractmethod
    def get_config_path(self):
        pass
