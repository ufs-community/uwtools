"""
Common iotaa tasks.
"""

import os
from pathlib import Path
from shutil import copy, which
from types import SimpleNamespace as ns
from typing import NoReturn, Union
from urllib.parse import urlparse

import requests
from iotaa import asset, external, task

from uwtools.exceptions import UWConfigError

SCHEMES = ns(http=("http", "https"), local=("", "file"))


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
def existing(path: Union[Path, str]):
    """
    An existing file, directory, symlink, or remote object.

    :param path: Path to the item.
    :raises: UWConfigError for unsupported URL schemes.
    """
    info = urlparse(str(path))
    scheme = info.scheme
    if scheme in SCHEMES.local:
        path = Path(info.path if scheme == "file" else path)
        yield "Filesystem item %s" % path
        yield asset(path, path.exists)
    elif scheme in SCHEMES.http:
        path = str(path)
        ready = lambda: requests.head(path, allow_redirects=True, timeout=3).status_code == 200
        yield "Remote object %s" % path
        yield asset(path, ready)
    else:
        _bad_scheme(scheme)


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


@task
def filecopy(src: Union[Path, str], dst: Union[Path, str]):
    """
    A copy of an existing file.

    :param src: Path to the source file.
    :param dst: Path to the destination file to create.
    :raises: UWConfigError for unsupported URL schemes.
    """
    yield "Copy %s -> %s" % (src, dst)
    yield asset(Path(dst), Path(dst).is_file)
    dst = Path(dst)  # currently no support for remote destinations
    scheme = urlparse(str(src)).scheme
    if scheme in SCHEMES.local:
        src = Path(src)
        yield file(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        copy(src, dst)
    elif scheme in SCHEMES.http:
        pass
    else:
        _bad_scheme(scheme)


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


# Private helpers


def _bad_scheme(scheme: str) -> NoReturn:
    """
    Fail on an unsupported URL scheme.

    :param scheme: The scheme.
    :raises: UWConfigError.
    """
    raise UWConfigError(f"Support for scheme '{scheme}' not implemented")
