from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ..config import HermesConfig


@dataclass
class MenuSelection:
    """Holds the selections made by the user in the menu."""
    session_name: str
    model: str
    budget: int
    prompt: str
    selected_server_name: Optional[str]  # None for local execution


class HermesResearchMenuInterface(ABC):
    @abstractmethod
    def set_config(self, config: HermesConfig):
        """Sets the configuration object needed for menu options."""
        pass

    @abstractmethod
    def get_selection(self) -> MenuSelection:
        """Runs the interactive menu and returns the user's selections."""
        pass
