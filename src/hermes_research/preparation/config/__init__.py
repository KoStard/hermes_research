from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class HermesConfigRemoteServer:
    hostname: str
    username: str
    remote_research_path: str


@dataclass
class HermesConfig:
    research_directory: str
    default_budget: int
    remote_servers: dict[str, HermesConfigRemoteServer]
    models: list[str]


class ConfigManagerInterface(ABC):
    @abstractmethod
    def load_config(self) -> HermesConfig:
        pass
    
    @abstractmethod
    def add_model(self, model_name: str) -> None:
        pass

    @abstractmethod
    def remove_model(self, model_name: str) -> None:
        pass

    @abstractmethod
    def set_research_directory(self, research_directory: str) -> None:
        pass

    @abstractmethod
    def set_default_budget(self, budget: int) -> None:
        pass

    @abstractmethod
    def add_remote_server(self, name, hostname, username, remote_research_path) -> None:
        pass

    @abstractmethod
    def remove_remote_server(self, name) -> None:
        pass

    @abstractmethod
    def initialize_default_config(self):
        pass
