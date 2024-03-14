# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import yaml
from pytest import fixture, raises

from uwtools import file
from uwtools.exceptions import UWConfigError


@fixture
def assets(tmp_path):
    srcdir = tmp_path / "src"
    srcdir.mkdir()
    fn1 = srcdir / "foo"
    fn1.touch()
    fn2 = srcdir / "subdir" / "bar"
    fn2.parent.mkdir()
    fn2.touch()
    config = {"a": {"b": {"foo": str(fn1), "subdir/bar": str(fn2)}}}
    cfgfile = tmp_path / "config.yaml"
    with open(cfgfile, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    dstdir = tmp_path / "dst"
    return dstdir, cfgfile


def test_FileStager(assets):
    dstdir, cfgfile = assets
    stager = file.FileStager(target_dir=dstdir, config_file=cfgfile, keys=["a", "b"])
    assert set(stager._file_map.keys()) == {"foo", "subdir/bar"}
    assert stager._validate() is True


def test_FileStager_bad_key(assets):
    dstdir, cfgfile = assets
    with raises(UWConfigError) as e:
        file.FileStager(target_dir=dstdir, config_file=cfgfile, keys=["a", "x"])
    assert str(e.value) == "Config navigation a -> x failed"


def test_FileCopier(assets):
    dstdir, cfgfile = assets
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    stager = file.FileCopier(target_dir=dstdir, config_file=cfgfile, keys=["a", "b"])
    stager.go()
    assert (dstdir / "foo").is_file()
    assert (dstdir / "subdir" / "bar").is_file()


def test_FileLinker(assets):
    dstdir, cfgfile = assets
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    stager = file.FileLinker(target_dir=dstdir, config_file=cfgfile, keys=["a", "b"])
    stager.go()
    assert (dstdir / "foo").is_symlink()
    assert (dstdir / "subdir" / "bar").is_symlink()
