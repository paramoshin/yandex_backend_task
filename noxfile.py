"""Nox sessions."""
import tempfile
from pathlib import Path
from typing import Any

import nox
from nox.sessions import Session

nox.options.sessions = "safety", "tests"
package = "ecommerce_analyzer"


def install_with_constraints(session: Session, *args: str, with_hashes: bool = True, **kwargs: Any) -> None:
    """Install packages constrained by Poetry's lock file.

    This function is a wrapper for nox.sessions.Session.install.
    It invokes pip to install packages inside of the session's virtualenv.
    Additionally, pip is passed a constraints file generated from Poetry's lock file,
    to ensure that the packages are pinned to the versions specified in poetry.lock.
    This allows you to manage the packages as Poetry development dependencies.

    Arguments:
        session: The Session object.
        args: Command-line arguments for pip.
        with_hashes: If to export dependencies with hashes (might cause an error if true for some dependencies).
        kwargs: Additional keyword arguments for Session.install.

    """
    cmds = [
        "poetry",
        "export",
        "--dev",
        "--format=requirements.txt",
    ]
    if not with_hashes:
        cmds.append("--without-hashes")
    with tempfile.NamedTemporaryFile() as requirements:
        cmds.append(f"--output={requirements.name}")
        session.run(*cmds, external=True)
        session.install(f"--constraint={requirements.name}", *args, **kwargs)


@nox.session(python=["3.8"])
def safety(session: Session) -> None:
    """Scan dependecies for insecure packages."""
    with tempfile.NamedTemporaryFile() as requirements:
        session.run(
            "poetry",
            "export",
            "--dev",
            "--format=requirements.txt",
            "--without-hashes",
            f"--output={requirements.name}",
            external=True,
        )
        install_with_constraints(session, "safety", with_hashes=False)
        session.run("safety", "check", f"--file={requirements.name}", "--full-report")


@nox.session(python=["3.8"])
def tests(session: Session) -> None:
    """Run tests."""
    args = session.posargs or ["--cov"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "coverage[toml]", "pytest", "pytest-cov", "pytest-mock")
    session.run("pytest", *args)


@nox.session(python=["3.8"])
def xdoctest(session: Session) -> None:
    """Run examples with xdoctest."""
    args = session.posargs or ["all"]
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "pygments", with_hashes=False)
    install_with_constraints(session, "xdoctest", with_hashes=False)
    session.run("python", "-m", "xdoctest", package, *args)


@nox.session(python=["3.8"])
def docs(session: Session) -> None:
    """Build the documentation."""
    session.run("poetry", "install", "--no-dev", external=True)
    install_with_constraints(session, "pdoc3")
    session.run("pdoc", "--html", "--output-dir", "docs", package)
