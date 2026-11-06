import re
import tomllib
from pathlib import Path

import akashi

PYPROJECT = Path(__file__).parents[2] / "pyproject.toml"


def test_version_matches_pyproject() -> None:
    """The runtime version is the one declared in pyproject.toml."""
    declared = tomllib.loads(PYPROJECT.read_text())["project"]["version"]

    assert akashi.__version__ == declared


def test_version_is_semantic() -> None:
    """Release tags are derived from the version, so it must be MAJOR.MINOR.PATCH."""
    assert re.fullmatch(r"\d+\.\d+\.\d+", akashi.__version__)
