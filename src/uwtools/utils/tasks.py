"""
Common iotaa tasks.
"""

import os
from pathlib import Path
from shutil import copy

from iotaa import asset, external, task


@external
def file(path: Path):
    """
    An existing file.

    :param path: Path to the file.
    """
    yield "File %s" % path
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
    dst.parent.mkdir(exist_ok=True)
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
    yield file(target)
    linkname.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(src=target, dst=linkname)
