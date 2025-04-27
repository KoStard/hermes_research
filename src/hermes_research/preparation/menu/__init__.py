from abc import ABC, abstractmethod
from typing import Dict

class HermesResearchMenuInterface(ABC):
    @abstractmethod
    def set_config(self, config):
        pass
    
    @abstractmethod
    def get_selection() -> Dict[str, any]:
        pass
