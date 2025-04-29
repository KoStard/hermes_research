import pytest
from unittest.mock import MagicMock

from hermes_research.preparation.cli.hermes_research_cli import HermesResearchCLI

class TestHermesResearchCLI:
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mocked dependencies for the CLI."""
        return {
            "paths_manager": MagicMock(),
            "config_manager": MagicMock(),
            "menu": MagicMock(),
            "command_manager": MagicMock(),
            "tmux_manager": MagicMock(),
            "ssh_connection": MagicMock(),
            "session_name_manager": MagicMock()
        }
    
    @pytest.fixture
    def cli(self, mock_dependencies):
        """Create a CLI instance with mocked dependencies."""
        return HermesResearchCLI(**mock_dependencies)
    
    # Add CLI-specific tests here
