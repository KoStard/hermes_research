from argparse import ArgumentParser
from hermes_research.preparation.cli.hermes_research_cli import HermesResearchCLI


def main():
    cli = HermesResearchCLI()
    parser = ArgumentParser()
    cli.define_cli(parser)
    args = parser.parse_args()
    cli.execute(args)
