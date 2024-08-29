# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name

import iotaa
import yaml
from pytest import fixture, mark, raises

from uwtools import fs
from uwtools.exceptions import UWConfigError

# Fixtures


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


# Helpers


class ConcreteStager(fs.Stager):
    def _validate(self):
        pass

    @property
    def _dst_paths(self):
        return list(self._config.keys())

    @property
    def _schema(self):
        return "some-schema"


# Tests


@mark.parametrize("source", ("dict", "file"))
def test_Copier(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    fs.Copier(target_dir=dstdir, config=config, keys=["a", "b"]).go()
    assert (dstdir / "foo").is_file()
    assert (dstdir / "subdir" / "bar").is_file()


def test_Copier_config_file_dry_run(assets):
    dstdir, cfgdict, _ = assets
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    fs.Copier(target_dir=dstdir, config=cfgdict, keys=["a", "b"], dry_run=True).go()
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    iotaa.dryrun(False)


def test_Copier_no_targetdir_abspath_pass(assets):
    dstdir, cfgdict, _ = assets
    old = cfgdict["a"]["b"]
    cfgdict = {str(dstdir / "foo"): old["foo"], str(dstdir / "bar"): old["subdir/bar"]}
    assets = fs.Copier(config=cfgdict).go()
    assert all(asset.ready() for asset in assets)  # type: ignore


def test_Copier_no_targetdir_relpath_fail(assets):
    _, cfgdict, _ = assets
    with raises(UWConfigError) as e:
        fs.Copier(config=cfgdict, keys=["a", "b"]).go()
    errmsg = "Relative path '%s' requires the target directory to be specified"
    assert errmsg % "foo" in str(e.value)


@mark.parametrize("source", ("dict", "file"))
def test_FilerStager(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    assert fs.FileStager(target_dir=dstdir, config=config, keys=["a", "b"])


@mark.parametrize("source", ("dict", "file"))
def test_Linker(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    fs.Linker(target_dir=dstdir, config=config, keys=["a", "b"]).go()
    assert (dstdir / "foo").is_symlink()
    assert (dstdir / "subdir" / "bar").is_symlink()


@mark.parametrize("source", ("dict", "file"))
def test_Stager__config_block_fail_bad_key_path(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    with raises(UWConfigError) as e:
        ConcreteStager(target_dir=dstdir, config=config, keys=["a", "x"])
    assert str(e.value) == "Failed following YAML key(s): a -> x"


@mark.parametrize("val", [None, True, False, "str", 42, 3.14, [], tuple()])
def test_Stager__config_block_fails_bad_type(assets, val):
    dstdir, cfgdict, _ = assets
    cfgdict["a"]["b"] = val
    with raises(UWConfigError) as e:
        ConcreteStager(target_dir=dstdir, config=cfgdict, keys=["a", "b"])
    assert str(e.value) == "Expected block not found at key path: a.b"
