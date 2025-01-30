# pylint: disable=missing-function-docstring,redefined-outer-name

import datetime as dt
from pathlib import Path

from pytest import fixture

from uwtools.api import fs
from uwtools.strings import STR


@fixture
def kwargs(tmp_path):
    dstdir, srcdir = tmp_path / "dst", tmp_path / "src"
    srcfile1, srcfile2 = srcdir / "f1", srcdir / "f2"
    srcdir.mkdir()
    for f in [srcfile1, srcfile2]:
        f.touch()
    config = {"a": {"b": {str(dstdir / "f1"): str(srcfile1), str(dstdir / "f2"): str(srcfile2)}}}
    return {
        "target_dir": None,
        "config": config,
        "cycle": dt.datetime.now(),
        "leadtime": dt.timedelta(hours=6),
        "key_path": ["a", "b"],
        "dry_run": False,
    }


def test_copy_fail(kwargs):
    paths = kwargs["config"]["a"]["b"]
    for p in paths:
        assert not Path(p).exists()
    Path(list(paths.values())[0]).unlink()
    report = fs.copy(**kwargs)
    ready = Path(list(paths.keys())[1])
    assert ready.is_file()
    assert list(map(str, report[STR.ready])) == [str(ready)]
    not_ready = Path(list(paths.keys())[0])
    assert not not_ready.exists()
    assert list(map(str, report[STR.notready])) == [str(not_ready)]


def test_copy_pass(kwargs):
    paths = kwargs["config"]["a"]["b"]
    for p in paths:
        assert not Path(p).exists()
    report = fs.copy(**kwargs)
    for p in paths:
        assert Path(p).is_file()
    assert set(map(str, report[STR.ready])) == set(paths.keys())
    assert set(map(str, report[STR.notready])) == set()


def test_link_fail(kwargs):
    paths = kwargs["config"]["a"]["b"]
    assert not any(Path(p).exists() for p in paths)
    Path(list(paths.values())[0]).unlink()
    report = fs.link(**kwargs)
    ready = Path(list(paths.keys())[1])
    assert ready.is_symlink()
    assert list(map(str, report[STR.ready])) == [str(ready)]
    not_ready = Path(list(paths.keys())[0])
    assert not not_ready.exists()
    assert list(map(str, report[STR.notready])) == [str(not_ready)]


def test_link_pass(kwargs):
    paths = kwargs["config"]["a"]["b"]
    for p in paths:
        assert not Path(p).exists()
    report = fs.link(**kwargs)
    for p in paths:
        assert Path(p).is_symlink()
    assert set(map(str, report[STR.ready])) == set(paths.keys())
    assert set(map(str, report[STR.notready])) == set()


def test_makedirs(tmp_path):
    paths = [tmp_path / "foo" / x for x in ("bar", "baz")]
    assert not any(path.is_dir() for path in paths)
    assert fs.makedirs(config={"makedirs": [str(path) for path in paths]}) is True
    assert all(path.is_dir() for path in paths)
