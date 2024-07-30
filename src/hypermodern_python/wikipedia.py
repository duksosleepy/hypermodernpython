"""Client for the Wikipedia REST API, version 1."""

from __future__ import annotations

import asyncio
import sys
import textwrap
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from collections.abc import Awaitable

import httpx
from cattrs.preconf.orjson import make_converter
from loguru import logger
from prettier import cprint

if sys.version_info >= (3, 8):
    from importlib.metadata import metadata
else:
    from importlib_metadata import metadata

if sys.version_info >= (3, 9):
    from collections.abc import Iterable
else:
    from typing import Iterable

API_URL: str = (
    "https://{language}.wikipedia.org/api/rest_v1/page/random/summary"
)
USER_AGENT: str = "{Name}/{Version} (Contact: {Author-email})"
JSON: TypeAlias = (
    None | bool | int | float | str | list["JSON"] | dict[str, "JSON"]
)


def build_user_agent() -> str:
    fields = metadata("hypermodern_python")
    return USER_AGENT.format_map(fields)


@dataclass
class Page:
    """Page resource.

    Attributes:
        title: The title of the Wikipedia page.
        extract: A plain text summary.
    """

    title: str
    extract: str


@dataclass(slots=True)
class Fetcher:
    language: str = "en"
    url: str | None = None
    timeout: float | None = None
    headers: dict | None = None
    # These two are marked 'init=False' so they do not show up in the constructor  # noqa: E501
    # logic because the user doesn't need the ability to initialize these values since  # noqa: E501
    # they a.) have defaults and b.) are internal implementation details.
    client: httpx.AsyncClient = field(
        default_factory=httpx.AsyncClient, init=False
    )
    results: list[str] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        # Attach our timeout to our instance httpx client
        # (note how we need to do this in __post_init__ since we can't access
        #  peer instance variables in the `field()` defaults above because there's  # noqa: E501
        #  no `self` existing there yet)
        self.client.timeout = self.timeout
        if not self.url:
            self.url = API_URL.format(language=self.language)
        if not self.client.headers and self.headers:
            self.client.headers = self.headers
        self.client.http2 = True

    async def fetch(
        self, func: Awaitable[[httpx.AsyncClient, str], Page]
    ) -> None:
        async with self.client as client:
            tasks = [
                asyncio.ensure_future(func(client, self.url))
                for _ in range(1, 10)
            ]
            start_time = time.perf_counter()
            self.results: Iterable[JSON] = await asyncio.gather(*tasks)
            end_time = time.perf_counter()
            for page in self.results:
                cprint(page.title, fg="g")
                cprint(textwrap.fill(page.extract), fg="r")
                cprint("\n\n")
            logger.info(
                "[{} :: {}] Mission complete in {} seconds",
                self.url,
                len(self.results),
                end_time - start_time,
            )


converter = make_converter()


async def random_page(client: httpx.AsyncClient, url: str) -> Page:
    """Return a random page.

    Performs a GET request to the /page/random/summary endpoint.

    Args:
        client: httpx.AsyncClient
        url: str

    Returns:
        A page resource.

    Raises:
        The HTTP request failed or the HTTP response contained an invalid body.
    Example:
        >>> from hypermodern_python import wikipedia
        >>> page = wikipedia.random_page(language="en")
        >>> bool(page.title)
        True
    """
    try:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        data: JSON = response.json()
        return converter.structure(data, Page)
    except httpx.HTTPStatusError as error:
        raise error


headers = {"User-Agent": build_user_agent()}

fetch_wikipedia = Fetcher(timeout=100, headers=headers)
asyncio.run(fetch_wikipedia.fetch(random_page))
