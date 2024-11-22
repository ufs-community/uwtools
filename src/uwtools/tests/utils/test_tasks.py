# pylint: disable=missing-function-docstring

import os
import stat
from unittest.mock import patch

from uwtools.utils import tasks

# Tests


def test_tasks_directory(tmp_path):
    p = tmp_path / "foo" / "bar"
    assert not p.is_dir()
    assert tasks.directory(path=p).ready
    assert p.is_dir()


def test_tasks_executable(tmp_path):
    p = tmp_path / "program"
    # Ensure that only our temp directory is on the path:
    with patch.dict(os.environ, {"PATH": str(tmp_path)}, clear=True):
        # Program does not exist:
        assert not tasks.executable(program=p).ready
        # Program exists but is not executable:
        p.touch()
        assert not tasks.executable(program=p).ready
        # Program exists and is executable:
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)  # set executable bits
        assert tasks.executable(program=p).ready


def test_tasks_existing_missing(tmp_path):
    path = tmp_path / "x"
    assert not tasks.existing(path=path).ready


def test_tasks_existing_present_directory(tmp_path):
    path = tmp_path / "directory"
    path.mkdir()
    assert tasks.existing(path=path).ready


def test_tasks_existing_present_file(tmp_path):
    path = tmp_path / "file"
    path.touch()
    assert tasks.existing(path=path).ready


def test_tasks_existing_present_symlink(tmp_path):
    path = tmp_path / "symlink"
    path.symlink_to(os.devnull)
    assert tasks.existing(path=path).ready


def test_tasks_file_missing(tmp_path):
    path = tmp_path / "file"
    assert not tasks.file(path=path).ready


def test_tasks_file_present(tmp_path):
    path = tmp_path / "file"
    path.touch()
    assert tasks.file(path=path).ready


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
