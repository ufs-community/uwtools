# pylint: disable=missing-function-docstring

from iotaa import refs

from uwtools.utils import tasks


def test_tasks_file_missing(tmp_path):
    path = tmp_path / "file"
    assert not path.is_file()
    asset_id = refs(tasks.file(path=path))
    assert asset_id == path
    assert not asset_id.is_file()


def test_tasks_file_present(tmp_path):
    path = tmp_path / "file"
    path.touch()
    assert path.is_file()
    asset_id = refs(tasks.file(path=path))
    assert asset_id == path
    assert asset_id.is_file()


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
