from abc import ABC, abstractmethod

class SSHConnectionInterface(ABC):
    @abstractmethod
    def start_connection(self, destination):
        pass
    
    @abstractmethod
    def stop_connection(self):
        pass
    
    @abstractmethod
    def execute_command_on_remote(self, command):
        pass
