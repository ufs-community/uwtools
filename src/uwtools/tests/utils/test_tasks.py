# pylint: disable=missing-function-docstring

import logging
import os
import stat
from pathlib import Path
from unittest.mock import Mock, patch

from iotaa import asset, external
from pytest import mark, raises

from uwtools.exceptions import UWConfigError
from uwtools.tests.support import logged
from uwtools.utils import tasks

# Helpers


@external
def exists(x):
    yield x
    yield asset(x, lambda: True)


def ready(taskval):
    return taskval.ready()


# Tests


def test_tasks_directory(tmp_path):
    p = tmp_path / "foo" / "bar"
    assert not p.is_dir()
    assert ready(tasks.directory(path=p))
    assert p.is_dir()


def test_tasks_executable(tmp_path):
    p = tmp_path / "program"
    # Ensure that only our temp directory is on the path:
    with patch.dict(os.environ, {"PATH": str(tmp_path)}, clear=True):
        # Program does not exist:
        assert not ready(tasks.executable(program=p))
        # Program exists but is not executable:
        p.touch()
        assert not ready(tasks.executable(program=p))
        # Program exists and is executable:
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)  # set executable bits
        assert ready(tasks.executable(program=p))


@mark.parametrize("prefix", ["", "file://"])
def test_tasks_existing_local_missing(caplog, prefix, tmp_path):
    logging.getLogger().setLevel(logging.INFO)
    base = tmp_path / "x"
    path = prefix + str(base) if prefix else base
    assert not ready(tasks.existing(path=path))
    assert logged(caplog, "Filesystem item %s: State: Not Ready (external asset)" % base)


def test_tasks_existing_local_present_directory(caplog, tmp_path):
    logging.getLogger().setLevel(logging.INFO)
    path = tmp_path / "directory"
    path.mkdir()
    assert ready(tasks.existing(path=path))
    assert logged(caplog, "Filesystem item %s: State: Ready" % path)


@mark.parametrize("prefix", ["", "file://"])
def test_tasks_existing_local_present_file(caplog, prefix, tmp_path):
    logging.getLogger().setLevel(logging.INFO)
    base = tmp_path / "file"
    base.touch()
    path = prefix + str(base) if prefix else base
    assert ready(tasks.existing(path=path))
    assert logged(caplog, "Filesystem item %s: State: Ready" % base)


@mark.parametrize("prefix", ["", "file://"])
def test_tasks_existing_local_present_symlink(caplog, prefix, tmp_path):
    logging.getLogger().setLevel(logging.INFO)
    base = tmp_path / "symlink"
    base.symlink_to(os.devnull)
    path = prefix + str(base) if prefix else base
    assert ready(tasks.existing(path=path))
    assert logged(caplog, "Filesystem item %s: State: Ready" % base)


@mark.parametrize("scheme", ["http", "https"])
@mark.parametrize("code,expected", [(200, True), (404, False)])
def test_tasks_existing_remote(caplog, code, expected, scheme):
    logging.getLogger().setLevel(logging.INFO)
    path = f"{scheme}://foo.com/obj"
    with patch.object(tasks.requests, "head", return_value=Mock(status_code=code)) as head:
        state = ready(tasks.existing(path=path))
        assert state is expected
    head.assert_called_with(path, allow_redirects=True, timeout=3)
    msg = "Remote object %s: State: %s" % (path, "Ready" if state else "Not Ready (external asset)")
    assert logged(caplog, msg)


def test_tasks_file_missing(tmp_path):
    path = tmp_path / "file"
    assert not ready(tasks.file(path=path))


def test_tasks_file_present(tmp_path):
    path = tmp_path / "file"
    path.touch()
    assert ready(tasks.file(path=path))


def test_tasks_filecopy_simple(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.touch()
    assert not dst.is_file()
    tasks.filecopy(src=src, dst=dst)
    assert dst.is_file()


def test_tasks_filecopy_directory_hierarchy(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "foo" / "bar" / "dst"
    src.touch()
    assert not dst.is_file()
    tasks.filecopy(src=src, dst=dst)
    assert dst.is_file()


@mark.parametrize(
    "src,ok",
    [("/src/file", True), ("file:///src/file", True), ("foo://bucket/a/b", False)],
)
def test_tasks_filecopy_source_local(src, ok):
    dst = "/dst/file"
    if ok:
        with patch.object(tasks, "file", exists):
            with patch.object(tasks, "copy") as copy:
                with patch.object(tasks.Path, "mkdir") as mkdir:
                    tasks.filecopy(src=src, dst=dst)
        mkdir.assert_called_once_with(parents=True, exist_ok=True)
        copy.assert_called_once_with(Path(src), Path(dst))
    else:
        with raises(UWConfigError) as e:
            tasks.filecopy(src=src, dst=dst)
        assert str(e.value) == "Support for scheme 'foo' not implemented"


def test_tasks_symlink_simple(tmp_path):
    target = tmp_path / "target"
    link = tmp_path / "link"
    target.touch()
    assert not link.is_file()
    tasks.symlink(target=target, linkname=link)
    assert link.is_symlink()


def test_tasks_symlink_directory_hierarchy(tmp_path):
    target = tmp_path / "target"
    link = tmp_path / "foo" / "bar" / "link"
    target.touch()
    assert not link.is_file()
    tasks.symlink(target=target, linkname=link)
    assert link.is_symlink()
