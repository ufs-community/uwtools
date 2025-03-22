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
from uwtools.logging import log
from uwtools.strings import STR
from uwtools.utils.processing import run_shell_cmd

SCHEMES = ns(
    hsi=(STR.url_scheme_hsi,),
    http=(STR.url_scheme_http, STR.url_scheme_https),
    local=("", STR.url_scheme_file),
)


@task
def directory(path: Path):
    """
    A filesystem directory.

    :param path: Path to the directory.
    """
    yield "Directory %s" % path
    yield asset(path, path.is_dir)
    yield None
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        log.error(str(e))


@external
def executable(program: Union[Path, str]):
    """
    An executable program located on the current path.

    :param program: Name of or path to the program.
    """
    yield "Executable program '%s' on PATH" % program
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
        path = _local_path(path)
        yield "Filesystem item %s" % path
        yield asset(path, path.exists)
    elif scheme in SCHEMES.http:
        path = str(path)
        ready = lambda: requests.head(path, allow_redirects=True, timeout=3).status_code == 200
        yield "Remote object %s" % path
        yield asset(path, ready)
    else:
        _bad_scheme(path, scheme)


@external
def file(path: Union[Path, str], context: str = ""):
    """
    An existing file or symlink to an existing file.

    :param path: Path to the file.
    :param context: Optional additional context for the file.
    """
    path = _local_path(path)
    suffix = f" ({context})" if context else ""
    yield "File %s%s" % (path, suffix)
    yield asset(path, path.is_file)


@external
def file_hpss(path: Union[Path, str]):
    """
    An existing file in HPSS.

    :param path: HPSS path to the file.
    """
    yield "HPSS file %s" % path
    available, _ = run_shell_cmd(f"{STR.hsi} -q ls {str(path)}")
    yield asset(path, lambda: available)


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
    dst = _local_path(dst)  # currently no support for remote destinations
    parts = urlparse(str(src))
    src_scheme = parts.scheme
    if src_scheme in SCHEMES.hsi:
        yield [executable(STR.hsi), file_hpss(parts.path)]
        _filecopy_hsi(parts.path, dst)
    elif src_scheme in SCHEMES.http:
        yield existing(src)
        _filecopy_http(str(src), dst)
    elif src_scheme in SCHEMES.local:
        yield file(src)
        _filecopy_local(_local_path(src), dst)
    else:
        _bad_scheme(src, src_scheme)


@task
def symlink(target: Union[Path, str], linkname: Union[Path, str]):
    """
    A symbolic link.

    :param target: The existing file or directory.
    :param linkname: The symlink to create.
    """
    target, linkname = map(_local_path, [target, linkname])
    yield "Link %s -> %s" % (linkname, target)
    yield asset(linkname, linkname.exists)
    yield existing(target)
    linkname.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(
        src=target if target.is_absolute() else os.path.relpath(target, linkname.parent),
        dst=linkname,
    )


# Private helpers


def _bad_scheme(path: Union[Path, str], scheme: str) -> NoReturn:
    """
    Fail on an unsupported URL scheme.

    :param path: The path with a bad scheme.
    :param scheme: The scheme.
    :raises: UWConfigError.
    """
    raise UWConfigError(f"Scheme '{scheme}' in '{path}' not supported")


def _filecopy_hsi(src: str, dst: Path) -> None:
    """
    Copy an HPSS mass-store file to the local filesystem via HSI.

    :param src: HPSS path of the source file.
    :param dst: Path to the destination file to create.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    _, output = run_shell_cmd(f"{STR.hsi} -q get {dst} : {src}")
    for line in output.strip().split("\n"):
        log.info("=> %s", line)


def _filecopy_http(src: str, dst: Path) -> None:
    """
    Copy a remote file to the local filesystem via HTTP.

    :param src: URL of the source file.
    :param dst: Path to the destination file to create.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(src, allow_redirects=True, timeout=3)
    if (code := response.status_code) == 200:
        with open(dst, "wb") as f:
            f.write(response.content)
    else:
        log.error("Could not get '%s', HTTP status was: %s", src, code)


def _filecopy_local(src: Path, dst: Path) -> None:
    """
    Copy a file in the local filesystem.

    :param src: Path to the source file.
    :param dst: Path to the destination file to create.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    copy(src, dst)


def _local_path(path: Union[Path, str]) -> Path:
    """
    Ensure path is local and return simple version.

    :param path: The local path to check.
    :raises: UWConfigError if a non-local scheme is specified.
    """
    info = urlparse(str(path))
    if info.scheme and info.scheme not in SCHEMES.local:
        _bad_scheme(path, info.scheme)
    return Path(info.path)
