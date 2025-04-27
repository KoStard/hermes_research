from abc import ABC, abstractmethod
from argparse import ArgumentParser

class HermesResearchCLIInterface(ABC):
    @abstractmethod
    def define_cli(self, parser: ArgumentParser):
        pass

    @abstractmethod
    def execute(self, args):
        pass
