# pylint: disable=missing-function-docstring

from importlib import resources
from pathlib import Path


def fixture_path(suffix: str = "") -> Path:
    with resources.as_file(resources.files("uwtools.test.fixtures")) as prefix:
        path = prefix / suffix
    return path


def fixture_posix(suffix: str = "") -> str:
    return fixture_path(suffix).as_posix()


def fixture_uri(suffix: str = "") -> str:
    return fixture_path(suffix).as_uri()
