"""
Helpers for working with files and directories.
"""

import logging
import os
import shutil
import sys
from contextlib import contextmanager
from datetime import datetime as dt
from pathlib import Path
from types import SimpleNamespace as ns
from typing import IO, Generator

from uwtools.types import DefinitePath, OptionalPath

FORMAT = ns(
    atparse="atparse",
    bash="ini",
    cfg="ini",
    fieldtable="fieldtable",
    ini="ini",
    jinja2="jinja2",
    nml="nml",
    sh="ini",
    yaml="yaml",
    yml="yaml",
)


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
        logging.critical(msg)
        raise RuntimeError(msg) from e

    # Try to rename existing run directory if option is rename.

    try:
        if action == "rename" and os.path.isdir(directory):
            now = dt.now()
            save_dir = "%s%s" % (directory, now.strftime("_%Y%m%d_%H%M%S"))
            shutil.move(directory, save_dir)
    except (FileExistsError, RuntimeError) as e:
        msg = f"Could not rename directory {directory}"
        logging.critical(msg)
        raise RuntimeError(msg) from e


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
    msg = f"Cannot determine file type from unrecognized extension '{suffix}'"
    logging.critical(msg)
    raise ValueError(msg)


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
def readable(filepath: OptionalPath = None, mode: str = "r") -> Generator[IO, None, None]:
    """
    If a path to a file is specified, open it and return a readable handle; if not, return readable
    stdin.

    :param filepath: The path to a file to read.
    """
    if filepath:
        with open(filepath, mode, encoding="utf-8") as f:
            yield f
    else:
        yield sys.stdin


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
