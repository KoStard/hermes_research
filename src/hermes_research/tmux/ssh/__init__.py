from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple


@dataclass
class SSHDestination:
    username: str
    hostname: str

class SSHConnectionInterface(ABC):
    @abstractmethod
    def test_connection(self, destination: SSHDestination) -> bool:
        pass

    @abstractmethod
    def execute_command_on_remote(self, command: str, destination: SSHDestination) -> Tuple[str, str, int]:
        """
        Executes a command on the remote destination via SSH.

        Args:
            command: The command string to execute.
            destination: The SSH destination details.

        Returns:
            A tuple containing (stdout, stderr, return_code).
        
        Raises:
            Exceptions related to SSH connection or command execution failures 
            if the implementation chooses to raise them directly instead of 
            returning a non-zero return code.
        """
        pass
