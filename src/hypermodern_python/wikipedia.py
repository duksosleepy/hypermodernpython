"""Client for the Wikipedia REST API, version 1."""

import sys

if sys.version_info >= (3, 8):
    from importlib.metadata import metadata
else:
    from importlib_metadata import metadata

import asyncio
from dataclasses import dataclass, field
from typing import Awaitable

import desert
import httpx
import marshmallow
from loguru import logger

API_URL: str = (
    "https://{language}.wikipedia.org/api/rest_v1/page/random/summary"
)
USER_AGENT: str = "{Name}/{Version} (Contact: {Author-email})"


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


schema = desert.schema(Page, meta={"unknown": marshmallow.EXCLUDE})


@dataclass(slots=True)
class Fetcher:
    language: str = "en"
    url: str | None = None
    timeout: float | None = None
    headers: dict | None
    # These two are marked 'init=False' so they do not show up in the constructor  # noqa: E501
    # logic because the user doesn't need the ability to initialize these values since  # noqa: E501
    # they a.) have defaults and b.) are internal implementation details.
    client: httpx.Client = field(
        default_factory=httpx.AsyncClient(), init=False
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
        if not self.client.headers and not self.headers:
            self.client.headers = {"User-Agent": build_user_agent()}
        self.client.http2 = True

    async def fetch(
        self, func: Awaitable[httpx.AsyncClient(), str, str]
    ) -> None:
        async with self.client as client:
            tasks = []
            for number in range(1, 10):
                tasks.append(
                    asyncio.ensure_future(
                        func(client, self.url, language=self.language)
                    )
                )

            self.results = await asyncio.gather(*tasks)
            for page in self.results:
                print(page)
            logger.info(
                "[{} :: {}] Mission complete",
                self.url,
                len(self.results),
            )


async def random_page(
    client: httpx.AsyncClient(), url: str, language: str = "en"
) -> Page:
    """Return a random page.

    Performs a GET request to the /page/random/summary endpoint.

    Args:
        language: The Wikipedia language edition. By default, the English
            Wikipedia is used ("en").

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
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        return schema.load(data)
    except marshmallow.ValidationError as error:
        message = str(error)
        raise message


fetch_wikipedia = Fetcher(timeout=100)
asyncio.run(fetch_wikipedia.fetch(random_page))
