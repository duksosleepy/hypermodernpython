"""Command-line interface."""

import textwrap

from prettier import cprint

from . import wikipedia


def cmd() -> None:
    from jsonargparse import CLI

    CLI(wikipedia.Fetcher)


def main(language: str) -> None:
    """The hypermodern Python project."""
    page = wikipedia.random_page(language=language)
    cprint(page.title, fg="g")
    cprint(textwrap.fill(page.extract))
