"""Client for the Wikipedia REST API, version 1."""

import asyncio
from dataclasses import dataclass, field

import desert
import httpx
import marshmallow
from loguru import logger

API_URL: str = (
    "https://{language}.wikipedia.org/api/rest_v1/page/random/summary"
)


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
    url: str
    timeout: float | None = None

    # These two are marked 'init=False' so they do not show up in the constructor  # noqa: E501
    # logic because the user doesn't need the ability to initialize these values since  # noqa: E501
    # they a.) have defaults and b.) are internal implementation details.
    client: httpx.Client = field(default_factory=httpx.Client, init=False)
    results: list[str] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        # Attach our timeout to our instance httpx client
        # (note how we need to do this in __post_init__ since we can't access
        #  peer instance variables in the `field()` defaults above because there's  # noqa: E501
        #  no `self` existing there yet)
        self.client.timeout = self.timeout

    def fetch(self) -> None:
        logger.info("[{}] Fetching with timeout {}", self.url, self.timeout)

        self.results.append(self.client.get(self.url))

        logger.info(
            "[{} :: {}] Found results: {}",
            self.url,
            len(self.results),
            self.results,
        )


async def random_page(
    client: httpx.AsyncClient(), language: str = "en"
) -> Page:
    """Return a random page.

    Performs a GET request to the /page/random/summary endpoint.

    Args:
        language: The Wikipedia language edition. By default, the English
            Wikipedia is used ("en").

    Returns:
        A page resource.

    Raises:
        ClickException: The HTTP request failed or the HTTP response
            contained an invalid body.
    Example:
        >>> from hypermodern_python import wikipedia
        >>> page = wikipedia.random_page(language="en")
        >>> bool(page.title)
        True
    """
    url = API_URL.format(language=language)

    try:
        response = await client.get(url)
        data = response.json()
        return schema.load(data)
    except marshmallow.ValidationError as error:
        message = str(error)
        raise message


async def main() -> None:
    async with httpx.AsyncClient() as client:
        tasks = []
        for number in range(1, 10):
            tasks.append(
                asyncio.ensure_future(random_page(client, language="en"))
            )

        original_page = await asyncio.gather(*tasks)
        for page in original_page:
            print(page)


asyncio.run(main())
