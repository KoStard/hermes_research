from abc import ABC, abstractmethod
from argparse import ArgumentParser

class HermesResearchCLIInterface(ABC):
    @abstractmethod
    def define_cli(self, parser: ArgumentParser):
        # Accept the filepaths
        # Accept additional arguments with -c "...", that gets passed to the hermes directly
        pass

    @abstractmethod
    def execute(self, args):
        pass


class ConfigCLIInterface(ABC):
    @abstractmethod
    def define_cli(self, subparsers):
        """Define the configuration subcommands and arguments.
        
        Args:
            subparsers: argparse subparsers object to add commands to
        """
        pass
    
    @abstractmethod
    def execute(self, args):
        """Execute the configuration command based on parsed arguments.
        
        Args:
            args: The parsed command line arguments
        """
        pass
