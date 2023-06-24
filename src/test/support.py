# pylint: disable=missing-function-docstring

from importlib import resources
from pathlib import Path


def fixpath(suffix: str = "") -> Path:
    with resources.as_file(resources.files("fixtures")) as prefix:
        path = prefix / suffix
    return path


def fixpath_posix(suffix: str = "") -> str:
    return fixpath(suffix).as_posix()


def fixpath_uri(suffix: str = "") -> str:
    return fixpath(suffix).as_uri()
