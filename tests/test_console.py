import io
import subprocess
import sys
from unittest.mock import Mock

import pytest
from factory import Factory, Faker
from hypermodern_python import Page
from pytest_mock import MockFixture


@pytest.fixture
def file():
    return io.StringIO()


def parametrized_fixture(*params):
    return pytest.fixture(params=params)(lambda request: request.param)


class ArticleFactory(Factory):
    class Meta:
        model = Page

    title = Faker("sentence")
    summary = Faker("paragraph")


article = parametrized_fixture(*ArticleFactory.build_batch(10))


def test_final_newline(article, file):
    show(article, file)
    assert file.getvalue().endswith("\n")


@pytest.fixture
def serve(httpserver):
    def f(article):
        json = {"title": article.title, "extract": article.summary}
        httpserver.expect_request("/").respond_with_json(json)
        return httpserver.url_for("/")

    return f


def test_fetch(article, serve):
    assert article == fetch(serve(article))


def test_output():
    args = [sys.executable, "-m", "random_wikipedia_article"]
    process = subprocess.run(args, capture_output=True, check=True)
    assert process.stdout


@pytest.fixture
def mock_requests_get(mocker):
    mock = mocker.patch("requests.get")
    mock.return_value.__enter__.return_value.json.return_value = {
        "title": "Lorem Ipsum",
        "extract": "Lorem ipsum dolor sit amet",
    }
    return mock


@pytest.fixture
def mock_wikipedia_random_page(mocker: MockFixture) -> Mock:
    return mocker.patch("hypermodern_python.wikipedia.random_page")
