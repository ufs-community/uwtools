# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import pytest
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
    cfgdict = {"a": {"b": {"foo": str(fn1), "subdir/bar": str(fn2)}}}
    cfgfile = tmp_path / "config.yaml"
    with open(cfgfile, "w", encoding="utf-8") as f:
        yaml.dump(cfgdict, f)
    dstdir = tmp_path / "dst"
    return dstdir, cfgdict, cfgfile


@pytest.mark.parametrize("source", ("dict", "file"))
def test_FileStager(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    stager = file.FileStager(target_dir=dstdir, config=config, keys=["a", "b"])
    assert set(stager._file_map.keys()) == {"foo", "subdir/bar"}
    assert stager._validate() is True


@pytest.mark.parametrize("source", ("dict", "file"))
def test_FileStager_bad_key(assets, source):
    dstdir, cfgfile, cfgdict = assets
    config = cfgdict if source == "dict" else cfgfile
    with raises(UWConfigError) as e:
        file.FileStager(target_dir=dstdir, config=config, keys=["a", "x"])
    assert str(e.value) == "Config navigation a -> x failed"


@pytest.mark.parametrize("source", ("dict", "file"))
def test_FileCopier_config_file(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    stager = file.FileCopier(target_dir=dstdir, config=config, keys=["a", "b"])
    stager.go()
    assert (dstdir / "foo").is_file()
    assert (dstdir / "subdir" / "bar").is_file()


@pytest.mark.parametrize("source", ("dict", "file"))
def test_FileLinker_config_file(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    stager = file.FileLinker(target_dir=dstdir, config=config, keys=["a", "b"])
    stager.go()
    assert (dstdir / "foo").is_symlink()
    assert (dstdir / "subdir" / "bar").is_symlink()
