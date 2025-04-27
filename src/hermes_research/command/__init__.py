from abc import ABC, abstractmethod
from typing import List

class HermesResearchCommandManagerInterface(ABC):
    @abstractmethod
    def generate_command(self, path_to_research: str, model: str, files: List[str], budget: int, prompt: str, extra_arguments: str) -> str:
        """
        extra_arguments is a string that contains the extra arguments to be passed directly to the hermes command.
        """
        pass
    
    @abstractmethod
    def save_command_in_file(self, command, path):
        pass
