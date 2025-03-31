# pylint: disable=missing-function-docstring,protected-access

import logging
import os
import stat
from pathlib import Path
from typing import Union
from unittest.mock import ANY, Mock, patch

import iotaa
from iotaa import asset, external
from pytest import mark, raises

from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.strings import STR
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


def test_utils_tasks_directory__fail(logged, tmp_path):
    os.chmod(tmp_path, 0o550)
    p = tmp_path / "foo"
    assert not iotaa.ready(tasks.directory(path=p))
    assert not p.is_dir()
    os.chmod(tmp_path, 0o750)
    assert logged("[Errno 13] Permission denied: '%s'" % p)


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


@mark.parametrize("available", [True, False])
@mark.parametrize("wrapper", [Path, str])
def test_utils_tasks_existing_hpss(available, wrapper):
    path = wrapper("/path/to/file")
    with (
        patch.object(tasks, "executable", exists),
        patch.object(tasks, "run_shell_cmd", return_value=(available, None)) as run_shell_cmd,
    ):
        val = tasks.existing_hpss(path=path)
    assert iotaa.refs(val) == path
    taskname = f"HPSS file {path}"
    run_shell_cmd.assert_called_once_with(f"{STR.hsi} -q ls -1 '{path}'", taskname=taskname)


@mark.parametrize("scheme", ["http", "https"])
@mark.parametrize("code,expected", [(200, True), (404, False)])
def test_utils_tasks_existing_http(code, expected, logged, scheme):
    log.setLevel(logging.INFO)
    url = f"{scheme}://foo.com/obj"
    with patch.object(tasks.requests, "head", return_value=Mock(status_code=code)) as head:
        state = iotaa.ready(tasks.existing_http(url=url))
        assert state is expected
    head.assert_called_with(url, allow_redirects=True, timeout=3)
    msg = "Remote HTTP resource %s: %s" % (url, "Ready" if state else "Not ready [external asset]")
    assert logged(msg)


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
    with patch.object(tasks, "existing_http", exists):
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
    with patch.object(tasks, "filecopy_hsi") as filecopy_hsi:
        tasks.filecopy(src=src, dst=dst_in)
    filecopy_hsi.assert_called_once_with("/path/to/file", Path(dst_out), True)


@mark.parametrize(
    ["dst_in", "dst_out"],
    [("/path/to/dst", "/path/to/dst"), ("file:///path/to/dst", "/path/to/dst")],
)
def test_utils_tasks_filecopy__mocked_htar(dst_in, dst_out):
    src = "htar:///path/to/archive.tar?foo%3F%26bar"
    with patch.object(tasks, "filecopy_htar") as filecopy_htar:
        tasks.filecopy(src=src, dst=dst_in)
    filecopy_htar.assert_called_once_with("/path/to/archive.tar", "foo?&bar", Path(dst_out), True)


@mark.parametrize("scheme", ["http", "https"])
@mark.parametrize(
    ["dst_in", "dst_out"],
    [("/path/to/dst", "/path/to/dst"), ("file:///path/to/dst", "/path/to/dst")],
)
def test_utils_tasks_filecopy__mocked_http(scheme, dst_in, dst_out):
    src = f"{scheme}://foo.com/obj"
    with patch.object(tasks, "filecopy_http") as filecopy_http:
        tasks.filecopy(src=src, dst=dst_in)
    filecopy_http.assert_called_once_with(src, Path(dst_out), True)


@mark.parametrize(
    ["src_in", "src_out"],
    [("/path/to/src", "/path/to/src"), ("file:///path/to/src", "/path/to/src")],
)
@mark.parametrize(
    ["dst_in", "dst_out"],
    [("/path/to/dst", "/path/to/dst"), ("file:///path/to/dst", "/path/to/dst")],
)
def test_utils_tasks_filecopy__mocked_local(src_in, src_out, dst_in, dst_out):
    with patch.object(tasks, "filecopy_local") as filecopy_local:
        tasks.filecopy(src=src_in, dst=dst_in)
    filecopy_local.assert_called_once_with(Path(src_out), Path(dst_out), True)


def test_utils_tasks_filecopy__simple(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.touch()
    assert not dst.is_file()
    tasks.filecopy(src=src, dst=dst)
    assert dst.is_file()


def test_utils_tasks_filecopy_hsi(logged, ready_task, tmp_path):
    log.setLevel(logging.INFO)
    src = "/path/to/src"
    dst = tmp_path / "dst"
    with (
        patch.object(tasks, "run_shell_cmd") as run_shell_cmd,
        patch.object(tasks, "existing_hpss", wraps=ready_task) as existing_hpss,
    ):
        run_shell_cmd.side_effect = lambda *_a, **_kw: (dst.touch(), (True, "msg1\nmsg2\n"))[1]
        tasks.filecopy_hsi(src=src, dst=Path(dst))
    existing_hpss.assert_called_once_with(src)
    taskname = f"HSI {src} -> {dst}"
    run_shell_cmd.assert_called_once_with(f"hsi -q get '{dst}' : '{src}'", taskname=taskname)
    assert logged(f"{taskname}: => msg1")
    assert logged(f"{taskname}: => msg2")
    assert dst.exists()


def test_utils_tasks_filecopy_htar(logged, ready_task, tmp_path):
    log.setLevel(logging.INFO)
    src_archive = "/path/to/archive.tar"
    src_file = "afile"
    dst = tmp_path / "dst"
    with (
        patch.object(tasks, "existing_hpss", wraps=ready_task) as existing_hpss,
        patch.object(tasks, "move", side_effect=lambda *_a, **_kw: dst.touch()) as move,
        patch.object(tasks, "run_shell_cmd", return_value=(True, "msg1\nmsg2\n")) as run_shell_cmd,
    ):
        tasks.filecopy_htar(src_archive=src_archive, src_file=src_file, dst=Path(dst))
    existing_hpss.assert_called_once_with(src_archive)
    cmd = f"htar -qxf '{src_archive}' '{src_file}'"
    taskname = f"HTAR {src_archive}:{src_file} -> {dst}"
    run_shell_cmd.assert_called_once_with(cmd, cwd=ANY, taskname=taskname)
    move.assert_called_once_with(ANY, dst)
    assert logged(f"{taskname}: => msg1")
    assert logged(f"{taskname}: => msg2")
    assert dst.exists()


def test_utils_tasks_filecopy_http(ready_task, tmp_path):
    dst = tmp_path / "dst"
    url = "http://foo.com/obj"
    assert not dst.exists()
    with (
        patch.object(tasks.requests, "get") as get,
        patch.object(tasks, "existing_http", wraps=ready_task) as existing_http,
    ):
        response = Mock(status_code=200, content=b"data")
        get.return_value = response
        tasks.filecopy_http(url=url, dst=dst)
    existing_http.assert_called_once_with(url)
    get.assert_called_once_with(url, allow_redirects=True, timeout=3)
    assert dst.exists()


def test_utils_tasks_filecopy_local(tmp_path):
    src = tmp_path / "src"
    src.touch()
    dst = tmp_path / "subdir" / "dst"
    assert not dst.exists()
    tasks.filecopy_local(src=src, dst=dst)
    assert dst.exists()


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


@mark.parametrize("wrapper", [Path, str])
def test_utils_tasks_symlink_target(tmp_path, wrapper):
    d, f, s = (tmp_path / x for x in ("d", "f", "s"))
    d.mkdir()
    f.touch()
    s.symlink_to(f)
    for x in [d, f, s]:
        assert iotaa.ready(tasks.symlink_target(path=wrapper(x)))
    assert not iotaa.ready(tasks.symlink_target(path=tmp_path / "foo"))


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
