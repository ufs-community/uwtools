import datetime as dt
from pathlib import Path

from pytest import fixture

from uwtools.api import fs
from uwtools.strings import STR

# Fixtures


@fixture
def kwargs(tmp_path, utc):
    dstdir, srcdir = tmp_path / "dst", tmp_path / "src"
    srcfile1, srcfile2 = srcdir / "f1", srcdir / "f2"
    srcdir.mkdir()
    for f in [srcfile1, srcfile2]:
        f.touch()
    config = {"a": {"b": {str(dstdir / "f1"): str(srcfile1), str(dstdir / "f2"): str(srcfile2)}}}
    return {
        "target_dir": None,
        "config": config,
        "cycle": utc(),
        "leadtime": dt.timedelta(hours=6),
        "key_path": ["a", "b"],
        "dry_run": False,
    }


# Tests


def test_fs_copy_fail(kwargs):
    paths = kwargs["config"]["a"]["b"]
    for p in paths:
        assert not Path(p).exists()
    Path(list(paths.values())[0]).unlink()
    report = fs.copy(**kwargs)
    ready = Path(list(paths.keys())[1])
    assert ready.is_file()
    assert set(report[STR.ready]) == {str(ready)}
    not_ready = Path(list(paths.keys())[0])
    assert not not_ready.exists()
    assert set(report[STR.notready]) == {str(not_ready)}


def test_fs_copy_pass(kwargs):
    paths = kwargs["config"]["a"]["b"]
    for p in paths:
        assert not Path(p).exists()
    report = fs.copy(**kwargs)
    for p in paths:
        assert Path(p).is_file()
    assert set(report[STR.ready]) == set(paths.keys())
    assert set(report[STR.notready]) == set()


def test_fs_link_fail(kwargs):
    paths = kwargs["config"]["a"]["b"]
    assert not any(Path(p).exists() for p in paths)
    Path(list(paths.values())[0]).unlink()
    report = fs.link(**kwargs)
    ready = Path(list(paths.keys())[1])
    assert ready.is_symlink()
    assert set(report[STR.ready]) == {str(ready)}
    not_ready = Path(list(paths.keys())[0])
    assert not not_ready.exists()
    assert set(report[STR.notready]) == {str(not_ready)}


def test_fs_link_pass(kwargs):
    paths = kwargs["config"]["a"]["b"]
    for p in paths:
        assert not Path(p).exists()
    report = fs.link(**kwargs)
    for p in paths:
        assert Path(p).is_symlink()
    assert set(report[STR.ready]) == set(paths.keys())
    assert set(report[STR.notready]) == set()


def test_fs_makedirs_pass(tmp_path):
    paths = [tmp_path / "foo" / x for x in ("bar", "baz")]
    assert not any(path.is_dir() for path in paths)
    report = fs.makedirs(config={"makedirs": [str(path) for path in paths]})
    assert all(path.is_dir() for path in paths)
    assert set(report[STR.ready]) == set(map(str, paths))
    assert set(report[STR.notready]) == set()


def test_fs_makedirs_fail(tmp_path):
    paths = [tmp_path / "foo" / x for x in ("bar", "baz")]
    assert not any(path.is_dir() for path in paths)
    tmp_path.chmod(0o555)  # make tmp_path read-only
    report = fs.makedirs(config={"makedirs": [str(path) for path in paths]})
    assert not any(path.is_dir() for path in paths)
    assert set(report[STR.ready]) == set()
    assert set(report[STR.notready]) == set(map(str, paths))
    tmp_path.chmod(0o755)  # make tmp_path writable
