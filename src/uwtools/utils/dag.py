"""
Helpers for iotaa workflows.
"""

from pathlib import Path
from typing import Generator

from iotaa import asset, external, task


@task
def directory(path: Path) -> Generator:
    """
    A filesystem directory, which will be created if not already present.

    :param path: The path to the directory.
    """
    yield f"Directory: {path}"
    yield asset(path, path.is_dir)
    yield None
    path.mkdir(parents=True)


@external
def file(path: Path) -> Generator:
    """
    A filesystem file, which must already be present.

    :param path: The path to the file.
    """
    yield f"File: {path}"
    yield asset(path, path.is_file)
