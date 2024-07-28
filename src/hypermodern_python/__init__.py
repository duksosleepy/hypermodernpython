"""The hypermodern Python project."""

import argparse

__version__ = "0.2.0"


def main():
    parser = argparse.ArgumentParser(prog="random-wikipedia-article")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.parse_args()
