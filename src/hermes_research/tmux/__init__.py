from abc import ABC, abstractmethod
from typing import List

class TmuxManagerInterface(ABC):
    @abstractmethod
    def set_remote(self, destination: str):
        """
        If not set, the default is to use the local tmux server.
        """
        pass

    @abstractmethod
    def list_sessions(self) -> List[str]:
        pass

    @abstractmethod
    def session_exists(self, name: str) -> bool:
        """Checks if a tmux session with the given name exists."""
        pass

    @abstractmethod
    def create_session(self, name: str):
        pass

    @abstractmethod
    def send_command(self, session_name: str, command: str):
        pass

    @abstractmethod
    def kill_session(self, name: str):
        """Kills the tmux session with the given name."""
        pass
