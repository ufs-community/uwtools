"""
Common iotaa tasks.
"""

import os
from pathlib import Path
from shutil import copy, which
from typing import Union

from iotaa import asset, external, task


@task
def directory(path: Path):
    """
    A filesystem directory.

    :param path: Path to the directory.
    """
    yield "Directory %s" % path
    yield asset(path, path.is_dir)
    yield None
    path.mkdir(parents=True, exist_ok=True)


@external
def executable(program: Union[Path, str]):
    """
    An executable program located on the current path.

    :param program: Name of or path to the program.
    """
    yield "Executable program %s" % program
    yield asset(program, lambda: bool(which(program)))


@external
def existing(path: Path):
    """
    An existing filesystem item (file, directory, or symlink).

    :param path: Path to the item.
    """
    yield "Filesystem item %s" % path
    yield asset(path, path.exists)


@external
def file(path: Path, pathstr: str = ""):
    """
    An existing file or symlink to an existing file.

    :param path: Path to the file.
    """
    prefix = pathstr + ": " if pathstr else ""
    yield "%sFile %s" % (prefix, path)
    yield asset(path, path.is_file)


@task
def filecopy(src: Path, dst: Path):
    """
    A copy of an existing file.

    :param src: Path to the source file.
    :param dst: Path to the destination file to create.
    """
    yield "Copy %s -> %s" % (src, dst)
    yield asset(dst, dst.is_file)
    yield file(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    copy(src, dst)


@task
def symlink(target: Path, linkname: Path):
    """
    A symbolic link.

    :param target: The existing file or directory.
    :param linkname: The symlink to create.
    """
    yield "Link %s -> %s" % (linkname, target)
    yield asset(linkname, linkname.exists)
    yield existing(target)
    linkname.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(
        src=target if target.is_absolute() else os.path.relpath(target, linkname.parent),
        dst=linkname,
    )
