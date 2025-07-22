"""
Common iotaa tasks.
"""

from __future__ import annotations

import os
from http import HTTPStatus
from pathlib import Path
from shutil import copy, move, which
from tempfile import TemporaryDirectory
from types import SimpleNamespace as ns
from typing import NoReturn
from urllib.parse import unquote, urlparse

import requests
from iotaa import Node, asset, external, task

from uwtools.exceptions import UWConfigError, UWError
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
def executable(program: Path | str):
    """
    An executable program located on the current path.

    :param program: Name of or path to the program.
    """
    yield "Executable program '%s' on PATH" % program
    yield asset(program, lambda: bool(which(program)))


@task
def existing_hpss(path: Path | str):
    """
    An existing file in HPSS.

    :param path: HPSS path to the file.
    """
    taskname = "HPSS file %s" % path
    yield taskname
    val = [False]
    yield asset(path, lambda: val[0])
    yield executable(STR.hsi)
    available, _ = run_shell_cmd(f"{STR.hsi} -q ls -1 '{path!s}'", taskname=taskname)
    val[0] = available


@external
def existing_http(url: str):
    """
    An existing remote HTTP resource.

    :param url: URL of the HTTP resource.
    """
    yield "Remote HTTP resource %s" % url
    yield asset(
        url,
        lambda: requests.head(url, allow_redirects=True, timeout=3).status_code == HTTPStatus.OK,
    )


@external
def file(path: Path | str, context: str = ""):
    """
    An existing file.

    :param path: Path to the file.
    :param context: Optional additional context for the file.
    """
    path = _local_path(path)
    suffix = f" ({context})" if context else ""
    yield "File %s%s" % (path, suffix)
    yield asset(path, path.is_file)


def filecopy(src: Path | str, dst: Path | str, check: bool = True) -> Node:
    """
    A copy of an existing file.

    :param src: Path to the source file.
    :param dst: Path to the destination file to create.
    :param check: Check existence of source before trying to copy.
    :return: An iotaa task-graph node.
    :raises: UWConfigError for unsupported URL schemes.
    """
    dst = _local_path(dst)  # currently no support for remote destinations
    parts = urlparse(str(src))
    src_scheme = parts.scheme
    if src_scheme in SCHEMES.hsi:
        return filecopy_hsi(parts.path, dst, check)
    if src_scheme in SCHEMES.htar:
        return filecopy_htar(parts.path, unquote(parts.query), dst, check)
    if src_scheme in SCHEMES.http:
        return filecopy_http(str(src), dst, check)
    if src_scheme in SCHEMES.local:
        return filecopy_local(_local_path(src), dst, check)
    return _bad_scheme(src, src_scheme)


@task
def filecopy_hsi(src: str, dst: Path, check: bool = True):
    """
    Copy an HPSS file to the local filesystem via hsi.

    :param src: HPSS path to the source file.
    :param dst: Path to the destination file to create.
    :param check: Check existence of source before trying to copy.
    """
    taskname = "HSI %s -> %s" % (src, dst)
    yield taskname
    yield asset(Path(dst), Path(dst).is_file)
    yield existing_hpss(src) if check else None
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = f"{STR.hsi} -q get '{dst}' : '{src}'"
    _, output = run_shell_cmd(cmd, taskname=taskname)
    for line in output.strip().split("\n"):
        log.info("%s: => %s", taskname, line)


@task
def filecopy_htar(src_archive: str, src_file: str, dst: Path, check: bool = True):
    """
    Copy a file from an HPSS-based archive to the local filesystem via htar.

    :param src_archive: HPSS path to the source archive.
    :param src_file: Path within the archive to the file.
    :param dst: Path to the destination file to create.
    :param check: Check existence of source before trying to copy.
    """
    taskname = "HTAR %s:%s -> %s" % (src_archive, src_file, dst)
    yield taskname
    yield asset(Path(dst), Path(dst).is_file)
    yield existing_hpss(src_archive) if check else None
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = f"{STR.htar} -qxf '{src_archive}' '{src_file}'"
    with TemporaryDirectory(prefix=".tmpdir", dir=dst.parent) as tmpdir:
        _, output = run_shell_cmd(cmd, cwd=tmpdir, taskname=taskname)
        for line in output.strip().split("\n"):
            log.info("%s: => %s", taskname, line)
        tmp = Path(tmpdir, src_file)
        log.info("%s: Moving %s -> %s", taskname, tmp, dst)
        move(tmp, dst)


@task
def filecopy_http(url: str, dst: Path, check: bool = True):
    """
    Copy a remote file to the local filesystem via HTTP.

    :param url: URL of the source file.
    :param dst: Path to the destination file to create.
    :param check: Check existence of source before trying to copy.
    """
    yield "HTTP %s -> %s" % (url, dst)
    yield asset(dst, dst.is_file)
    yield existing_http(url) if check else None
    dst.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, allow_redirects=True, stream=True, timeout=3)
    if (code := response.status_code) == HTTPStatus.OK:
        with dst.open(mode="wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        log.error("Could not get '%s', HTTP status was: %s", url, code)


@task
def filecopy_local(src: Path, dst: Path, check: bool = True):
    """
    Copy a file in the local filesystem.

    :param src: Path to the source file.
    :param dst: Path to the destination file to create.
    :param check: Check existence of source before trying to copy.
    """
    yield "Local %s -> %s" % (src, dst)
    yield asset(Path(dst), Path(dst).is_file)
    yield file(src) if check else None
    dst.parent.mkdir(parents=True, exist_ok=True)
    copy(src, dst)


@task
def hardlink(
    target: Path | str, linkname: Path | str, check: bool = True, symlink_fallback: bool = False
):
    """
    A hardlink.

    :param target: The existing file or directory.
    :param linkname: The symlink to create.
    :param check: Check existence of source before trying to link.
    :param symlink_fallback: Create symlinks when hardlinks cannot be created?
    """
    target, linkname = map(_local_path, [target, linkname])
    yield "Hardlink %s -> %s" % (linkname, target)
    yield asset(linkname, linkname.exists)
    yield link_target(target) if check else None
    linkname.parent.mkdir(parents=True, exist_ok=True)
    src = target if target.is_absolute() else os.path.relpath(target, linkname.parent)
    dst = linkname
    try:
        os.link(src, dst)
    except OSError as e:
        if symlink_fallback:
            os.symlink(src, dst)
        else:
            raise UWError("Could not hardlink %s -> %s" % (src, dst)) from e


@task
def symlink(target: Path | str, linkname: Path | str, check: bool = True):
    """
    A symbolic link.

    :param target: The existing file or directory.
    :param linkname: The symlink to create.
    :param check: Check existence of source before trying to link.
    """
    target, linkname = map(_local_path, [target, linkname])
    yield "Symlink %s -> %s" % (linkname, target)
    yield asset(linkname, linkname.exists)
    yield link_target(target) if check else None
    linkname.parent.mkdir(parents=True, exist_ok=True)
    src = target if target.is_absolute() else os.path.relpath(target, linkname.parent)
    dst = linkname
    os.symlink(src, dst)


@external
def link_target(path: Path | str):
    """
    An existing file, link, or directory.

    :param path: Path to the file, link, or directory.
    :param context: Optional additional context for the file.
    """
    path = _local_path(path)
    yield "Target %s" % path
    yield asset(path, path.exists)


# Private helpers


def _bad_scheme(path: Path | str, scheme: str) -> NoReturn:
    """
    Fail on an unsupported URL scheme.

    :param path: The path with a bad scheme.
    :param scheme: The scheme.
    :raises: UWConfigError.
    """
    msg = f"Scheme '{scheme}' in '{path}' not supported"
    raise UWConfigError(msg)


def _local_path(path: Path | str) -> Path:
    """
    Ensure path is local and return simple version.

    :param path: The local path to check.
    :raises: UWConfigError if a non-local scheme is specified.
    """
    info = urlparse(str(path))
    if info.scheme and info.scheme not in SCHEMES.local:
        _bad_scheme(path, info.scheme)
    return Path(info.path)
