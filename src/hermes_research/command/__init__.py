from abc import ABC, abstractmethod
from typing import List

class HermesResearchCommandManagerInterface(ABC):
    @abstractmethod
    def generate_command(self, path_to_research: str, model: str, files: List[str], budget: int, prompt: str) -> str:
        pass
    
    @abstractmethod
    def save_command_in_file(self, command, path):
        pass
