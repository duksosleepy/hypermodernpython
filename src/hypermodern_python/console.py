"""Command-line interface."""

from __future__ import annotations

from . import wikipedia


def cmd() -> None:
    from jsonargparse import CLI

    CLI(wikipedia.Fetcher)
