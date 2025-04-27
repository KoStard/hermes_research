from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SSHDestination:
    username: str
    hostname: str

class SSHConnectionInterface(ABC):
    @abstractmethod
    def test_connection(self, destination: SSHDestination) -> bool:
        pass

    @abstractmethod
    def execute_command_on_remote(self, command: str, destionation: SSHDestination):
        pass
