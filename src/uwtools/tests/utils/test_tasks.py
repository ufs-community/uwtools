# pylint: disable=missing-function-docstring

import os

from uwtools.utils import tasks


def test_tasks_existing_missing(tmp_path):
    path = tmp_path / "x"
    assert not tasks.existing(path=path).ready()  # type: ignore # pylint: disable=no-member


def test_tasks_existing_present_directory(tmp_path):
    path = tmp_path / "directory"
    path.mkdir()
    assert tasks.existing(path=path).ready()  # type: ignore # pylint: disable=no-member


def test_tasks_existing_present_file(tmp_path):
    path = tmp_path / "file"
    path.touch()
    assert tasks.existing(path=path).ready()  # type: ignore # pylint: disable=no-member


def test_tasks_existing_present_symlink(tmp_path):
    path = tmp_path / "symlink"
    path.symlink_to(os.devnull)
    assert tasks.existing(path=path).ready()  # type: ignore # pylint: disable=no-member


def test_tasks_file_missing(tmp_path):
    path = tmp_path / "file"
    assert not tasks.file(path=path).ready()  # type: ignore # pylint: disable=no-member


def test_tasks_file_present(tmp_path):
    path = tmp_path / "file"
    path.touch()
    assert tasks.file(path=path).ready()  # type: ignore # pylint: disable=no-member


def test_tasks_filecopy(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.touch()
    assert not dst.is_file()
    tasks.filecopy(src=src, dst=dst)
    assert dst.is_file()


def test_tasks_symlink(tmp_path):
    target = tmp_path / "target"
    link = tmp_path / "link"
    target.touch()
    assert not link.is_file()
    tasks.symlink(target=target, linkname=link)
    assert link.is_symlink()
