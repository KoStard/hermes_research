from abc import ABC, abstractmethod
from typing import List

class TmuxManagerInterface(ABC):
    @abstractmethod
    def set_remote(self, destination: str):
        pass
    
    @abstractmethod
    def list_sessions(self) -> List[str]:
        pass
    
    @abstractmethod
    def create_session(self, name: str):
        pass
    
    @abstractmethod
    def send_command(self, session_name: str, command: str):
        pass

    @abstractmethod
    def determine_alternative_name(self, rejected_session_name: str) -> str:
        pass
