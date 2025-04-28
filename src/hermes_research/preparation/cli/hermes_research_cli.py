from argparse import ArgumentParser
from hermes_research.preparation.cli import HermesResearchCLIInterface


class HermesResearchCLI(HermesResearchCLIInterface):
    def __init__(self):
        pass

    def define_cli(self, parser: ArgumentParser):
        parser.add_argument("files", help="Path to the files to be included", nargs="*")

    def execute(self, args):
        files = args.files
        
        # Get the config with ConfigManager
        # Get the selection with HermesResearchMenu
        # 1. If local:
        # Generate the command script with HermesResearchCommandManager
        # Start with TmuxManager
        # 2. If remote:
        # Setup a temporary folder in the remote server
        # Determine filenames for the attached files
        # Generate the command script with HermesResearchCommandManager considering the remote paths
        # Copy the files and the script to the remote server
        # Start the command in the remote server with TmuxManager