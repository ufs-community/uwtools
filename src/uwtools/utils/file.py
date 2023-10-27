"""
Helpers for working with files and directories.
"""

import os
import shutil
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime as dt
from functools import cache
from importlib import resources
from io import StringIO
from pathlib import Path
from typing import IO, Any, Generator, Union

from uwtools.logging import log
from uwtools.types import DefinitePath, OptionalPath


@dataclass(frozen=True)
class _FORMAT:
    """
    A mapping from config format names to literal strings.
    """

    # Canonical strings:

    _atparse: str = "atparse"
    _fieldtable: str = "fieldtable"
    _ini: str = "ini"
    _jinja2: str = "jinja2"
    _nml: str = "nml"
    _xml: str = "xml"
    _yaml: str = "yaml"

    # Variants:

    atparse: str = _atparse
    bash: str = _ini
    cfg: str = _ini
    fieldtable: str = _fieldtable
    ini: str = _ini
    jinja2: str = _jinja2
    nml: str = _nml
    sh: str = _ini
    yaml: str = _yaml
    yml: str = _yaml


FORMAT = _FORMAT()


class StdinProxy:
    """
    Reads stdin once but permits multiple reads of its data.
    """

    def __init__(self) -> None:
        self._stdin = sys.stdin.read()
        self._reset()

    def __getattr__(self, attr: str) -> Any:
        self._reset()
        return getattr(self._stringio, attr)

    def __iter__(self):
        self._reset()
        for line in self._stringio.read().split("\n"):
            yield line

    def _reset(self) -> None:
        self._stringio = StringIO(self._stdin)


@cache
def _stdinproxy():
    return StdinProxy()


def get_file_type(path: DefinitePath) -> str:
    """
    Returns a standardized file type given a path/filename.

    :param path: A path or filename.
    :return: One of a set of supported file types.
    :raises: ValueError if the path/filename suffix is unrecognized.
    """
    suffix = Path(path).suffix.replace(".", "")
    if fmt := vars(FORMAT).get(suffix):
        return fmt
    msg = f"Cannot deduce format of '{path}' from unknown extension '{suffix}'"
    log.critical(msg)
    raise ValueError(msg)


def handle_existing(directory: str, action: str) -> None:
    """
    Given a run directory, and an action to do if directory exists, delete or rename directory.

    :param directory: The directory to delete or rename.
    :param action: The action to take on an existing directory ("delete" or "rename")
    """

    # Try to delete existing run directory if option is delete.

    try:
        if action == "delete" and os.path.isdir(directory):
            shutil.rmtree(directory)
    except (FileExistsError, RuntimeError) as e:
        msg = f"Could not delete directory {directory}"
        log.critical(msg)
        raise RuntimeError(msg) from e

    # Try to rename existing run directory if option is rename.

    try:
        if action == "rename" and os.path.isdir(directory):
            now = dt.now()
            save_dir = "%s%s" % (directory, now.strftime("_%Y%m%d_%H%M%S"))
            shutil.move(directory, save_dir)
    except (FileExistsError, RuntimeError) as e:
        msg = f"Could not rename directory {directory}"
        log.critical(msg)
        raise RuntimeError(msg) from e


def path_if_it_exists(path: str) -> str:
    """
    Returns the given path as an absolute path if it exists, and raises an exception otherwise.

    :param path: The filesystem path to test.
    :return: The same filesystem path as an absolute path.
    :raises: FileNotFoundError is path does not exst
    """
    p = Path(path)
    if not p.exists():
        msg = f"{path} does not exist"
        print(msg, file=sys.stderr)
        raise FileNotFoundError(msg)
    return str(p.absolute())


@contextmanager
def readable(
    filepath: OptionalPath = None, mode: str = "r"
) -> Generator[Union[IO, StdinProxy], None, None]:
    """
    If a path to a file is specified, open it and return a readable handle; if not, return readable
    stdin.

    :param filepath: The path to a file to read.
    """
    if filepath:
        with open(filepath, mode, encoding="utf-8") as f:
            yield f
    else:
        yield _stdinproxy()


def resource_pathobj(suffix: str = "") -> Path:
    """
    Returns a pathlib Path object to a uwtools resource file.

    :param suffix: A subpath relative to the location of the uwtools resource files. The prefix path
        to the resources files is known to Python and varies based on installation location.
    """
    with resources.as_file(resources.files("uwtools.resources")) as prefix:
        return prefix / suffix


# def resource_path(suffix: str = "") -> str:
#     """
#     Returns a POSIX path to a uwtools resource file.

#:param suffix: A subpath relative to the location of the uwtools resource files. The prefix path
# to the resources files is known to Python and varies based on installation location.
#     """
#     return resource_pathobj(suffix).as_posix()


@contextmanager
def writable(filepath: OptionalPath = None, mode: str = "w") -> Generator[IO, None, None]:
    """
    If a path to a file is specified, open it and return a writable handle; if not, return writeable
    stdout.

    :param filepath: The path to a file to write to.
    """
    if filepath:
        with open(filepath, mode, encoding="utf-8") as f:
            yield f
    else:
        yield sys.stdout
