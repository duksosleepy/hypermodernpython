"""Nox sessions."""

from __future__ import annotations

import platform
import shutil
import sys
from pathlib import Path
from typing import Any

import nox

package = "hypermodern_python"
locations = "src", "tests", "noxfile.py", "docs/conf.py"
nox.options.error_on_external_run = True
nox.options.sessions = "lint", "safety"


def install_with_constraints(
    session: nox.Session, *args: str, **kwargs: Any
) -> None:
    """Install packages constrained by Poetry's lock file."""
    session.run(
        "poetry",
        "export",
        "--dev",
        "--format=requirements.txt",
        "--output=requirements.txt",
        external=True,
    )
    session.install("--constraint=requirements.txt", *args, **kwargs)


def install(session: nox.Session, groups: list[str], root: bool = True):
    if root:
        groups = ["main", *groups]
    session.run_install(
        "poetry",
        "install",
        "--no-root",
        "--sync",
        f"--only={','.join(groups)}",
        external=True,
    )
    if root:
        session.install(".")


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


def constraints(session: nox.Session):
    filename = f"python{session.python}-{sys.platform}-{platform.machine()}.txt"
    return Path("constraints") / filename


@nox.session
def build(session: nox.Session):
    """Build the package."""
    session.install("build", "twine")

    distdir = Path("dist")
    if distdir.exists():
        shutil.rmtree(distdir)

    session.run("python", "-m", "build")
    session.run("twine", "check", *distdir.glob("*"))


@nox.session(python=["3.12"])
def safety(session: nox.Session):
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


def install_coverage_pth(session: nox.Session):
    output = session.run(
        "python",
        "-c",
        "import sysconfig; print(sysconfig.get_path('purelib'))",
        silent=True,
    )
    purelib = Path(output.strip())
    (purelib / "_coverage.pth").write_text(
        "import coverage; coverage.process_startup()"
    )


@nox.session(python=["3.12"])
def tests(session: nox.Session):
    """Run the test suite."""
    args = session.posargs or ["--cov"]
    session.run("poetry", "install", external=True)
    session.run("pytest", *args)


@nox.session(python=["3.12"])
def tests_2(session: nox.Session):
    """Run the test suite."""
    session.install("-c", constraints(session), ".[tests]")
    install_coverage_pth(session)

    try:
        args = ["coverage", "run", "-m", "pytest", *session.posargs]
        session.run(*args, env={"COVERAGE_PROCESS_START": "pyproject.toml"})
    finally:
        session.notify("coverage")


@nox.session(python="3.12")
def lint(session: nox.Session):
    """Lint using pre-commit."""
    options = ["--all-files", "--show-diff-on-fail"]
    session.install(f"--constraint={constraints(session)}", "pre-commit")
    session.run("pre-commit", "run", *options, *session.posargs)


@nox.session(python=["3.12", "3.11", "3.10"])
def mypy(session: nox.Session) -> None:
    """Type-check using mypy."""
    session.install(f"--constraint={constraints(session)}", ".[typing,tests]")
    session.run("mypy", "src", "tests")
    session.run("mypy", f"--python-executable={sys.executable}", "noxfile.py")


@nox.session(python="3.12")
def typeguard(session: nox.Session) -> None:
    """Type-check using Typeguard."""
    session.install(
        f"--constraint={constraints(session)}", ".[tests]", "typeguard"
    )
    session.run("pytest", f"--typeguard-packages={package}")


@nox.session(python=["3.12"])
def black(session: nox.Session):
    """Run black code formatter."""
    args = session.posargs or locations
    session.install(
        "black"
    )  # also session.install("black==...") replace ... with version of packages you want
    session.run("black", *args)


@nox.session(python=["3.12"])
def pytype(session: nox.Session):
    """Type-check using pytype."""
    args = session.posargs or ["--disable=import-error", *locations]
    session.install("pytype")
    session.run("pytype", *args)


@nox.session(python=["3.12"])
def xdoctest(session: nox.Session) -> None:
    """Run examples with xdoctest."""
    args = session.posargs or ["all"]
    session.run("poetry", "install", "--no-dev", external=True)
    session.install("xdoctest")
    session.run("python", "-m", "xdoctest", package, *args)


@nox.session(python=["3.12"])
def docs(session: nox.Session) -> None:
    """Build the documentation."""
    session.run("poetry", "install", "--no-dev", external=True)
    session.install("sphinx", "sphinx-autodoc-typehints")
    session.run("sphinx-build", "docs", "docs/_build")


@nox.session(python=["3.12"])
def coverage(session: nox.Session) -> None:
    """Generate the coverage report."""
    session.install("-c", constraints(session), "coverage[toml]")
    if any(Path().glob(".coverage.*")):
        session.run("coverage", "combine")
    session.run("coverage", "report")
