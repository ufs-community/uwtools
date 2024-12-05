"""
Common iotaa tasks.
"""

import os
from pathlib import Path
from shutil import copy, which
from typing import Union
from urllib.parse import urlparse

from iotaa import asset, external, task

from uwtools.exceptions import UWConfigError


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
def file(path: Path, context: str = ""):
    """
    An existing file or symlink to an existing file.

    :param path: Path to the file.
    :param context: Optional additional context for the file.
    """
    suffix = f" ({context})" if context else ""
    yield "File %s%s" % (path, suffix)
    yield asset(path, path.is_file)


# >>> urlparse("path/to/file")
# ParseResult(scheme='', netloc='', path='path/to/file', params='', query='', fragment='')
# >>> urlparse("/path/to/file")
# ParseResult(scheme='', netloc='', path='/path/to/file', params='', query='', fragment='')
# >>> urlparse("file:///path/to/file")
# ParseResult(scheme='file', netloc='', path='/path/to/file', params='', query='', fragment='')
# >>> urlparse("https://foo.com/path/to/file")
# ParseResult(scheme='https', netloc='foo.com', path='/path/to/file', params='', query='',
#   fragment='')


@task
def filecopy(src: Union[Path, str], dst: Union[Path, str]):
    """
    A copy of an existing file.

    :param src: Path to the source file.
    :param dst: Path to the destination file to create.
    """
    yield "Copy %s -> %s" % (src, dst)
    yield asset(Path(dst), Path(dst).is_file)
    scheme = urlparse(str(src)).scheme
    if scheme in ("", "file"):
        src, dst = map(Path, [src, dst])
        yield file(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        copy(src, dst)
    else:
        raise UWConfigError(f"Support for scheme '{scheme}' not implemented")


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
