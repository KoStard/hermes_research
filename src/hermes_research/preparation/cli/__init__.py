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
