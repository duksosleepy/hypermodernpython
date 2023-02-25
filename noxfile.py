"""Nox sessions."""
import nox

from nox.sessions import Session

from typing import Any

package = "hypermodern_python"
locations = "src", "tests", "noxfile.py", "docs/conf.py"
nox.options.sessions = "lint", "mypy", "safety", "tests"


def install_with_constraints(session: Session, *args: str, **kwargs: Any) -> None:
    """Install packages constrained by Poetry's lock file."""
    session.run(
        "poetry",
        "export",
        "--dev",
        "--format=requirements.txt",
        f"--output=requirements.txt",
        external=True,
    )
    session.install("--constraint=requirements.txt", *args, **kwargs)


"""
@nox.session(python="[3.8]")
def black(session):
    args = session.posargs or locations
    install_with_constraints(session, "black")
    session.run("black", *args)
"""


"""
@nox.session(python=["3.11"])
def lint(session):
    args = session.posargs or locations
    install_with_constraints(
        session,
        "flake8",
        "flake8-bandit",
        "flake8-black",
        "flake8-bugbear",
        "flake8-import-order",
    )
    session.run("flake8", *args)
"""


"""
@nox.session(python="3.11")
def safety(session):
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            "--without-hashes",
            "--output=requirements.txt",
            external=True,
        )
        install_with_constraints(session, "safety")
        session.run("safety", "check", "--file=requirements.txt", "--full-report")
"""


@nox.session(python=["3.11"])
def safety(session):
    """Scan dependencies for insecure packages."""
    session.run(
        "poetry",
        "export",
        "--format=requirements.txt",
        "--without-hashes",
        "--output=requirements.txt",
        external=True,
    )
    session.install("safety")
    session.run("safety", "check", "--file=requirements.txt", "--full-report")


@nox.session(python=["3.11"])
def tests(session):
    """Run the test suite."""
    args = session.posargs or ["--cov"]
    session.run("poetry", "install", external=True)
    session.run("pytest", *args)


@nox.session(python=["3.11"])
def lint(session):
    """Lint using flake8."""
    args = session.posargs or locations
    session.install(
        "flake8",
        "flake8-black",
        "flake8-bandit",
        "flake8-bugbear",
        "flake8-isort",
        "flake8-annotations",
        "flake8-docstrings",
    )
    session.run("flake8", *args)


@nox.session(python=["3.11"])
def black(session):
    """Run black code formatter."""
    args = session.posargs or locations
    session.install(
        "black"
    )  # also session.install("black==...") replace ... with version of packages you want
    session.run("black", *args)


@nox.session(python=["3.11"])
def mypy(session):
    """Type-check using mypy."""
    args = session.posargs or locations
    session.install("mypy")
    session.run("mypy", *args)


@nox.session(python=["3.11"])
def pytype(session):
    """Type-check using pytype."""
    args = session.posargs or ["--disable=import-error", *locations]
    session.install("pytype")
    session.run("pytype", *args)


@nox.session(python=["3.11"])
def xdoctest(session: Session) -> None:
    """Run examples with xdoctest."""
    args = session.posargs or ["all"]
    session.run("poetry", "install", "--no-dev", external=True)
    session.install("xdoctest")
    session.run("python", "-m", "xdoctest", package, *args)


@nox.session(python=["3.11"])
def docs(session: Session) -> None:
    """Build the documentation."""
    session.run("poetry", "install", "--no-dev", external=True)
    session.install("sphinx", "sphinx-autodoc-typehints")
    session.run("sphinx-build", "docs", "docs/_build")


@nox.session(python=["3.11"])
def coverage(session: Session) -> None:
    """Upload coverage data."""
    session.install("coverage[toml]", "codecov")
    session.run("coverage", "xml", "--fail-under=0")
    session.run("codecov", *session.posargs)
