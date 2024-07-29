"""Command-line interface."""

from . import wikipedia


def cmd() -> None:
    from jsonargparse import CLI

    CLI(wikipedia.Fetcher)
