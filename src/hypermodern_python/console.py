"""Command-line interface."""

from __future__ import annotations

from jsonargparse import CLI

from .wikipedia import Fetcher, cli, random_page


def cmd() -> None:
    try:
        CLI(cli(Fetcher, random_page))
    except ValueError:
        pass
