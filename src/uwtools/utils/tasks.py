"""
Common iotaa tasks.
"""

import os
from pathlib import Path
from shutil import copy, move, which
from tempfile import TemporaryDirectory
from types import SimpleNamespace as ns
from typing import NoReturn, Union
from urllib.parse import urlparse

import requests
from iotaa import asset, external, task, tasks

from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.strings import STR
from uwtools.utils.processing import run_shell_cmd

SCHEMES = ns(
    hsi=(STR.url_scheme_hsi,),
    htar=(STR.url_scheme_htar,),
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


@task
def existing_hpss(path: Union[Path, str]):
    """
    An existing file in HPSS.

    :param path: HPSS path to the file.
    """
    yield "HPSS file %s" % path
    val = [False]
    yield asset(path, lambda: val[0])
    yield executable(STR.hsi)
    available, _ = run_shell_cmd(f"{STR.hsi} -q ls -1 '{str(path)}'")
    val[0] = available


@external
def existing_http(url: str):
    """
    An existing remote HTTP resource.

    :param url: URL of the HTTP resource.
    """
    yield "Remote HTTP resource %s" % url
    yield asset(url, lambda: requests.head(url, allow_redirects=True, timeout=3).status_code == 200)


@external
def file(path: Union[Path, str], context: str = ""):
    """
    An existing file.

    :param path: Path to the file.
    :param context: Optional additional context for the file.
    """
    path = _local_path(path)
    suffix = f" ({context})" if context else ""
    yield "File %s%s" % (path, suffix)
    yield asset(path, path.is_file)


@tasks
def filecopy(src: Union[Path, str], dst: Union[Path, str]):
    """
    A copy of an existing file.

    :param src: Path to the source file.
    :param dst: Path to the destination file to create.
    :raises: UWConfigError for unsupported URL schemes.
    """
    yield "Copy %s -> %s" % (src, dst)
    dst = _local_path(dst)  # currently no support for remote destinations
    parts = urlparse(str(src))
    src_scheme = parts.scheme
    if src_scheme in SCHEMES.hsi:
        yield filecopy_hsi(parts.path, dst)
    if src_scheme in SCHEMES.htar:
        yield filecopy_htar(parts.path, parts.query, dst)
    elif src_scheme in SCHEMES.http:
        yield filecopy_http(str(src), dst)
    elif src_scheme in SCHEMES.local:
        yield filecopy_local(_local_path(src), dst)
    else:
        _bad_scheme(src, src_scheme)


@task
def filecopy_hsi(src: str, dst: Path):
    """
    Copy an HPSS file to the local filesystem via hsi.

    :param src: HPSS path to the source file.
    :param dst: Path to the destination file to create.
    """
    taskname = "HSI %s -> %s" % (src, dst)
    yield taskname
    yield asset(Path(dst), Path(dst).is_file)
    yield existing_hpss(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _, output = run_shell_cmd(f"{STR.hsi} -q get '{dst}' : '{src}'")
    for line in output.strip().split("\n"):
        log.info("%s: => %s", taskname, line)


@task
def filecopy_htar(src_archive: str, src_file: str, dst: Path):
    """
    Copy a file from an HPSS-based archive to the local filesystem via htar.

    :param src_archive: HPSS path to the source archive.
    :param src_file: Path within the archive to the file.
    :param dst: Path to the destination file to create.
    """
    taskname = "HTAR %s:%s -> %s" % (src_archive, src_file, dst)
    yield taskname
    yield asset(Path(dst), Path(dst).is_file)
    yield existing_hpss(src_archive)
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = f"{STR.htar} -qxf '{src_archive}' '{src_file}'"
    with TemporaryDirectory(prefix=".tmpdir", dir=dst.parent) as tmpdir:
        _, output = run_shell_cmd(cmd, cwd=tmpdir)
        move(Path(tmpdir, src_file), dst)
    for line in output.strip().split("\n"):
        log.info("%s: => %s", taskname, line)


@task
def filecopy_http(url: str, dst: Path):
    """
    Copy a remote file to the local filesystem via HTTP.

    :param url: URL of the source file.
    :param dst: Path to the destination file to create.
    """
    yield "HTTP %s -> %s" % (url, dst)
    yield asset(Path(dst), Path(dst).is_file)
    yield existing_http(url)
    dst.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, allow_redirects=True, timeout=3)
    if (code := response.status_code) == 200:
        with open(dst, "wb") as f:
            f.write(response.content)
    else:
        log.error("Could not get '%s', HTTP status was: %s", url, code)


@task
def filecopy_local(src: Path, dst: Path):
    """
    Copy a file in the local filesystem.

    :param src: Path to the source file.
    :param dst: Path to the destination file to create.
    """
    yield "Local %s -> %s" % (src, dst)
    yield asset(Path(dst), Path(dst).is_file)
    yield file(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    copy(src, dst)


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
    yield symlink_target(target)
    linkname.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(
        src=target if target.is_absolute() else os.path.relpath(target, linkname.parent),
        dst=linkname,
    )


@external
def symlink_target(path: Union[Path, str]):
    """
    An existing file, symlink, or directory.

    :param path: Path to the file, symlink, or directory.
    :param context: Optional additional context for the file.
    """
    path = _local_path(path)
    yield "Target %s" % path
    yield asset(path, path.exists)


# Private helpers


def _bad_scheme(path: Union[Path, str], scheme: str) -> NoReturn:
    """
    Fail on an unsupported URL scheme.

    :param path: The path with a bad scheme.
    :param scheme: The scheme.
    :raises: UWConfigError.
    """
    raise UWConfigError(f"Scheme '{scheme}' in '{path}' not supported")


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
