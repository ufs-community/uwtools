# pylint: disable=missing-function-docstring,protected-access

import logging
import os
import stat
from pathlib import Path
from typing import Union
from unittest.mock import Mock, patch

import iotaa
from iotaa import asset, external
from pytest import mark, raises

from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.strings import STR
from uwtools.tests.support import logged
from uwtools.utils import tasks

# Helpers


@external
def exists(x):
    yield x
    yield asset(x, lambda: True)


# Tests


def test_utils_tasks_directory(tmp_path):
    p = tmp_path / "foo" / "bar"
    assert not p.is_dir()
    assert iotaa.ready(tasks.directory(path=p))
    assert p.is_dir()


def test_utils_tasks_directory__fail(caplog, tmp_path):
    os.chmod(tmp_path, 0o550)
    p = tmp_path / "foo"
    assert not iotaa.ready(tasks.directory(path=p))
    assert not p.is_dir()
    os.chmod(tmp_path, 0o750)
    assert logged(caplog, "[Errno 13] Permission denied: '%s'" % p)


def test_utils_tasks_executable(tmp_path):
    p = tmp_path / "program"
    # Ensure that only our temp directory is on the path:
    with patch.dict(os.environ, {"PATH": str(tmp_path)}, clear=True):
        # Program does not exist:
        assert not iotaa.ready(tasks.executable(program=p))
        # Program exists but is not executable:
        p.touch()
        assert not iotaa.ready(tasks.executable(program=p))
        # Program exists and is executable:
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)  # set executable bits
        assert iotaa.ready(tasks.executable(program=p))


def test_utils_tasks_existing__bad_scheme():
    path = "foo://bucket/a/b"
    with raises(UWConfigError) as e:
        tasks.existing(path=path)
    assert str(e.value) == f"Scheme 'foo' in '{path}' not supported"


@mark.parametrize("prefix", ["", "file://"])
def test_utils_tasks_existing__local_missing(caplog, prefix, tmp_path):
    log.setLevel(logging.INFO)
    base = tmp_path / "x"
    path = prefix + str(base) if prefix else base
    assert not iotaa.ready(tasks.existing(path=path))
    assert logged(caplog, "Filesystem item %s: Not ready [external asset]" % base)


def test_utils_tasks_existing__local_present_directory(caplog, tmp_path):
    log.setLevel(logging.INFO)
    path = tmp_path / "directory"
    path.mkdir()
    assert iotaa.ready(tasks.existing(path=path))
    assert logged(caplog, "Filesystem item %s: Ready" % path)


def test_utils_tasks_existing__missing(tmp_path):
    path = tmp_path / "x"
    assert not iotaa.ready(tasks.existing(path=path))


def test_utils_tasks_existing__present_file(tmp_path):
    path = tmp_path / "file"
    path.touch()
    assert iotaa.ready(tasks.existing(path=path))


def test_utils_tasks_existing__present_symlink(caplog, tmp_path):
    log.setLevel(logging.INFO)
    path = tmp_path / "symlink"
    path.symlink_to(os.devnull)
    assert iotaa.ready(tasks.existing(path=path))
    assert logged(caplog, "Filesystem item %s: Ready" % path)


@mark.parametrize("prefix", ["", "file://"])
def test_utils_tasks_existing__local_present_file(caplog, prefix, tmp_path):
    log.setLevel(logging.INFO)
    base = tmp_path / "file"
    base.touch()
    path = prefix + str(base) if prefix else base
    assert iotaa.ready(tasks.existing(path=path))
    assert logged(caplog, "Filesystem item %s: Ready" % base)


@mark.parametrize("prefix", ["", "file://"])
def test_utils_tasks_existing__local_present_symlink(caplog, prefix, tmp_path):
    log.setLevel(logging.INFO)
    base = tmp_path / "symlink"
    base.symlink_to(os.devnull)
    path = prefix + str(base) if prefix else base
    assert iotaa.ready(tasks.existing(path=path))
    assert logged(caplog, "Filesystem item %s: Ready" % base)


@mark.parametrize("scheme", ["http", "https"])
@mark.parametrize("code,expected", [(200, True), (404, False)])
def test_utils_tasks_existing__remote(caplog, code, expected, scheme):
    log.setLevel(logging.INFO)
    path = f"{scheme}://foo.com/obj"
    with patch.object(tasks.requests, "head", return_value=Mock(status_code=code)) as head:
        state = iotaa.ready(tasks.existing(path=path))
        assert state is expected
    head.assert_called_with(path, allow_redirects=True, timeout=3)
    msg = "Remote object %s: %s" % (path, "Ready" if state else "Not ready [external asset]")
    assert logged(caplog, msg)


@mark.parametrize("prefix", ["", "file://"])
def test_utils_tasks_file__missing(prefix, tmp_path):
    path = tmp_path / "file"
    path = "%s%s" % (prefix, path) if prefix else path
    assert not iotaa.ready(tasks.file(path=path))


@mark.parametrize("prefix", ["", "file://"])
def test_utils_tasks_file__present(prefix, tmp_path):
    path = tmp_path / "file"
    path.touch()
    path = "%s%s" % (prefix, path) if prefix else path
    assert iotaa.ready(tasks.file(path=path))


@mark.parametrize("available", [True, False])
@mark.parametrize("wrapper", [Path, str])
def test_utils_tasks_file_hpss(available, wrapper):
    path = wrapper("/path/to/file")
    with (
        patch.object(tasks, "executable", exists),
        patch.object(tasks, "run_shell_cmd", return_value=(available, None)) as run_shell_cmd,
    ):
        val = tasks.file_hpss(path=path)
    assert iotaa.refs(val) == path
    run_shell_cmd.assert_called_once_with(f"{STR.hsi} -q ls -1 '{path}'")


def test_utils_tasks_filecopy__directory_hierarchy(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "foo" / "bar" / "dst"
    src.touch()
    assert not dst.is_file()
    tasks.filecopy(src=src, dst=dst)
    assert dst.is_file()


@mark.parametrize("code,expected", [(200, True), (404, False)])
@mark.parametrize("src", ["http://foo.com/obj", "https://foo.com/obj"])
def test_utils_tasks_filecopy__source_http(code, expected, src, tmp_path):
    log.setLevel(logging.INFO)
    dst = tmp_path / "a-file"
    assert not dst.is_file()
    with patch.object(tasks, "existing", exists):
        with patch.object(tasks, "requests") as requests:
            response = requests.get()
            response.status_code = code
            response.content = "data".encode("utf-8")
            tasks.filecopy(src=src, dst=dst)
        requests.get.assert_called_with(src, allow_redirects=True, timeout=3)
    assert dst.is_file() is expected


@mark.parametrize(
    "src,ok",
    [("/src/file", True), ("file:///src/file", True), ("foo://bucket/a/b", False)],
)
def test_utils_tasks_filecopy__source_local(src, ok):
    dst = "/dst/file"
    with patch.object(tasks.Path, "mkdir") as mkdir:
        if ok:
            with patch.object(tasks, "file", exists):
                with patch.object(tasks, "copy") as copy:
                    tasks.filecopy(src=src, dst=dst)
            mkdir.assert_called_once_with(parents=True, exist_ok=True)
            copy.assert_called_once_with(Path("/src/file"), Path(dst))
        else:
            with raises(UWConfigError) as e:
                tasks.filecopy(src=src, dst=dst)
            assert str(e.value) == f"Scheme 'foo' in '{src}' not supported"


@mark.parametrize(
    ["dst_in", "dst_out"],
    [("/path/to/dst", "/path/to/dst"), ("file:///path/to/dst", "/path/to/dst")],
)
def test_utils_tasks_filecopy__mocked_hsi(dst_in, dst_out):
    src = "hsi:///path/to/file"
    with (
        patch.object(tasks, "_filecopy_hsi") as _filecopy_hsi,
        patch.object(tasks, "executable", exists),
        patch.object(tasks, "file_hpss", exists),
    ):
        tasks.filecopy(src=src, dst=dst_in)
    _filecopy_hsi.assert_called_once_with("/path/to/file", Path(dst_out))


@mark.parametrize("scheme", ["http", "https"])
@mark.parametrize(
    ["dst_in", "dst_out"],
    [("/path/to/dst", "/path/to/dst"), ("file:///path/to/dst", "/path/to/dst")],
)
def test_utils_tasks_filecopy__mocked_http(scheme, dst_in, dst_out):
    src = f"{scheme}://foo.com/obj"
    with (
        patch.object(tasks, "_filecopy_http") as _filecopy_http,
        patch.object(tasks, "existing", exists),
    ):
        tasks.filecopy(src=src, dst=dst_in)
    _filecopy_http.assert_called_once_with(src, Path(dst_out))


@mark.parametrize(
    ["src_in", "src_out"],
    [("/path/to/src", "/path/to/src"), ("file:///path/to/src", "/path/to/src")],
)
@mark.parametrize(
    ["dst_in", "dst_out"],
    [("/path/to/dst", "/path/to/dst"), ("file:///path/to/dst", "/path/to/dst")],
)
def test_utils_tasks_filecopy__mocked_local(src_in, src_out, dst_in, dst_out):
    with (
        patch.object(tasks, "_filecopy_local") as _filecopy_local,
        patch.object(tasks, "file", exists),
    ):
        tasks.filecopy(src=src_in, dst=dst_in)
    _filecopy_local.assert_called_once_with(Path(src_out), Path(dst_out))


def test_utils_tasks_filecopy__simple(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.touch()
    assert not dst.is_file()
    tasks.filecopy(src=src, dst=dst)
    assert dst.is_file()


@mark.parametrize("prefix", ["", "file://"])
def test_utils_tasks_symlink__simple(prefix, tmp_path):
    target = tmp_path / "target"
    link = tmp_path / "link"
    target.touch()
    assert not link.is_file()
    t2, l2 = ["%s%s" % (prefix, x) if prefix else x for x in (target, link)]
    tasks.symlink(target=t2, linkname=l2)
    assert link.is_symlink()


@mark.parametrize("prefix", ["", "file://"])
def test_utils_tasks_symlink__directory_hierarchy(prefix, tmp_path):
    target = tmp_path / "target"
    link = tmp_path / "foo" / "bar" / "link"
    target.touch()
    assert not link.is_file()
    t2, l2 = ["%s%s" % (prefix, x) if prefix else x for x in (target, link)]
    tasks.symlink(target=t2, linkname=l2)
    assert link.is_symlink()


def test_utils_tasks__filecopy_hsi(caplog, tmp_path):
    src = tmp_path / "src" / "foo"
    dst = tmp_path / "dst" / "foo"
    with patch.object(tasks, "run_shell_cmd") as run_shell_cmd:
        run_shell_cmd.return_value = (True, "foo\nbar\n")
        tasks._filecopy_hsi(src=src, dst=Path(dst))
    run_shell_cmd.assert_called_once_with(f"hsi -q get '{dst}' : '{src}'")
    assert logged(caplog, "=> foo")
    assert logged(caplog, "=> bar")


def test_utils_tasks__filecopy_http(tmp_path):
    dst = tmp_path / "dst"
    assert not dst.exists()
    with patch.object(tasks.requests, "get") as get:
        response = Mock(status_code=200, content=b"data")
        get.return_value = response
        tasks._filecopy_http(src="http://foo.com/obj", dst=dst)
    assert dst.exists()


def test_utils_tasks__filecopy_local(tmp_path):
    src = tmp_path / "src"
    src.touch()
    dst = tmp_path / "subdir" / "dst"
    assert not dst.exists()
    tasks._filecopy_local(src=src, dst=dst)
    assert dst.exists()


def test_utils_tasks__local__path_fail():
    path = "foo://bucket/a/b"
    with patch.object(tasks, "_bad_scheme") as _bad_scheme:
        tasks._local_path(path)
    _bad_scheme.assert_called_once_with(path, "foo")


@mark.parametrize("prefix", ["", "file://"])
@mark.parametrize("wrapper", [str, Path])
def test_utils_tasks__local__path_pass(prefix, wrapper):
    path = "/some/file"
    p2: Union[str, Path] = str(f"{prefix}{path}") if wrapper == str else Path(path)
    assert tasks._local_path(p2) == Path(path)
