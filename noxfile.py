import nox

import tempfile

locations = "src", "tests"
nox.options.sessions = "lint", "safety", "tests"


def install_with_constraints(session, *args, **kwargs):
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
    args = session.posargs or ["--cov"]
    session.run("poetry", "install", external=True)
    session.run("pytest", *args)


@nox.session(python=["3.11"])
def lint(session):
    args = session.posargs or locations
    session.install(
        "flake8", "flake8-black", "flake8-bandit", "flake8-bugbear", "flake8-isort"
    )
    session.run("flake8", *args)


@nox.session(python=["3.11"])
def black(session):
    args = session.posargs or locations
    session.install(
        "black"
    )  # also session.install("black==...") replace ... with version of packages you want
    session.run("black", *args)
