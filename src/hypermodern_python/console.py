"""Command-line interface."""

from __future__ import annotations

from jsonargparse import CLI

from . import wikipedia


def cmd() -> None:
    CLI(wikipedia.Fetcher)
