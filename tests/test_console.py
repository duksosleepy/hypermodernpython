from __future__ import annotations

import io
import subprocess
import sys
from collections.abc import Callable
from typing import Any, cast

import pytest
import pytest_httpserver
from factory import Factory, Faker

from hypermodern_python import Page


@pytest.fixture
def file() -> io.StringIO:
    return io.StringIO()


def parametrized_fixture(*params: Any) -> Any:
    return pytest.fixture(params=params)(lambda request: request.param)


class PageFactory(Factory):
    class Meta:
        model = Page

    title: Faker[Any, str] = Faker("sentence")
    extract: Faker[Any, str] = Faker("paragraph")


page = parametrized_fixture(Page("test"), *PageFactory.build_batch(10))


def test_final_newline(page: Page, file: io.StringIO) -> None:
    # show(article, file)
    assert file.getvalue().endswith("\n")


@pytest.fixture
def serve(httpserver: pytest_httpserver.HTTPServer) -> Callable[[Page], str]:
    def f(page: Page) -> str:
        json = {"title": page.title, "extract": page.extract}
        httpserver.expect_request("/").respond_with_json(json)
        return cast(str, httpserver.url_for("/"))

    return f


def test_fetch(page: Page, serve: Callable[[Page], str]) -> None:
    # assert page == fetch(serve(page))
    pass


def test_output() -> None:
    args = [sys.executable, "-m", "hypermodern_python"]
    process = subprocess.run(args, capture_output=True, check=True)
    assert process.stdout


def test_fetch_validates(
    page: Page, httpserver: pytest_httpserver.HTTPServer
) -> None:
    httpserver.expect_request("/").respond_with_json(None)
    with pytest.raises(TypeError):
        # fetch(httpserver.url_for("/"))
        pass
