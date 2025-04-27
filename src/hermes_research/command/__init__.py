from abc import ABC, abstractmethod
from typing import List

class HermesResearchCommandManagerInterface(ABC):
    @abstractmethod
    def generate_command(self, files: List[str], budget: int, prompt: str) -> str:
        pass
    
    @abstractmethod
    def save_command_in_file(self, command, path):
        pass
