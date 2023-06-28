# pylint: disable=missing-function-docstring

from importlib import resources
from pathlib import Path


def compare_files(expected: str, actual: str) -> bool:
    """
    Compare the content of two files. Prefer to filecmp.cmp when trailing
    newlines should be ignored. Print the two files to stdout when they do not
    match.
    """

    with open(expected, "r", encoding="utf-8") as expected_file:
        expected_content = expected_file.read().rstrip("\n")
    with open(actual, "r", encoding="utf-8") as actual_file:
        actual_content = actual_file.read().rstrip("\n")

    if expected_content != actual_content:
        print("The expected file looks like:")
        print(expected_content)
        print("*" * 80)
        print("The actual file looks like:")
        print(actual_content)
        return False
    return True


def fixture_pathobj(suffix: str = "") -> Path:
    with resources.as_file(resources.files("uwtools.test.fixtures")) as prefix:
        path = prefix / suffix
    return path


def fixture_path(suffix: str = "") -> str:
    return fixture_pathobj(suffix).as_posix()


def fixture_uri(suffix: str = "") -> str:
    return fixture_pathobj(suffix).as_uri()
