"""
Helpers for working with files and directories.
"""

import logging
import os
import shutil
import sys
from contextlib import contextmanager
from datetime import datetime as dt
from typing import IO, Generator

from uwtools.types import OptionalPath


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
