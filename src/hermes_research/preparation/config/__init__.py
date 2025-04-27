from abc import ABC, abstractmethod

class ConfigManagerInterface(ABC):
    @abstractmethod
    def load_config(self):
        pass
    
    @abstractmethod
    def set_config(self, key, value):
        pass
