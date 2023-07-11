# pylint: disable=missing-function-docstring

import re
from importlib import resources
from logging import LogRecord
from pathlib import Path
from typing import List


def compare_files(path1: str, path2: str) -> bool:
    """
    Determines whether the two given files are identical up to any number of trailing newlines,
    which are ignored. Print the contents of both files when they do not match.

    Parameters
    ----------
    path1
        Path to first file
    path2
        Path to second file

    Returns
    -------
    A bool indicating whether or not the files match.
    """
    with open(path1, "r", encoding="utf-8") as f:
        content1 = f.read().rstrip("\n")
    with open(path2, "r", encoding="utf-8") as f:
        content2 = f.read().rstrip("\n")
    if content1 != content2:
        print("1st file looks like:")
        print(content1)
        print("*" * 80)
        print("2nd file looks like:")
        print(content2)
        return False
    return True


def fixture_pathobj(suffix: str = "") -> Path:
    """
    Returns a pathlib Path object to a test-fixture resource file.

    Parameters
    ----------
    suffix
        A subpath relative to the location of the unit-test fixture resource
        files. The prefix path to the resources files is known to Python and
        varies based on installation location.
    """
    with resources.as_file(resources.files("uwtools.tests.fixtures")) as prefix:
        path = prefix / suffix
    return path


def fixture_path(suffix: str = "") -> str:
    """
    Returns a POSIX path to a test-fixture resource file.

    Parameters
    ----------
    suffix
        A subpath relative to the location of the unit-test fixture resource
        files. The prefix path to the resources files is known to Python and
        varies based on installation location.
    """
    return fixture_pathobj(suffix).as_posix()


def fixture_uri(suffix: str = "") -> str:
    """
    Returns a file:// URI path to a test-fixture resource file.

    Parameters
    ----------
    suffix
        A subpath relative to the location of the unit-test fixture resource
        files. The prefix path to the resources files is known to Python and
        varies based on installation location.
    """
    return fixture_pathobj(suffix).as_uri()


def line_in_lines(line: str, lines: List[str]) -> bool:
    """
    Determines whether the given line occurs, as a line-ending suffix, in any of the lines in the
    given list. For example, the line "bar" is a line-ending suffix of the line
    "[2023-06-29T14:06:34] foo", but not of the line "foo bar".

    Paramters
    ---------
    line:
        The sought-for line
    lines:
        The lines to be checked for the line

    Returns
    -------
    A bool indicating whether or not the line was found.
    """
    return any(x for x in lines if re.match(r"^.*%s$" % re.escape(line), x))


def msg_in_caplog(msg: str, records: List[LogRecord]) -> bool:
    """
    Determines whether the given message occurs in the given list of log records.

    Parameters
    ----------
    msg
        The sought-for message
    records
        The log records to be checked for the message

    Returns
    -------
    A bool indicating whether or not the message was found.
    """
    for record in records:
        if msg == record.msg:
            return True
    return False
