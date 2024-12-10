# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=redefined-outer-name

from pathlib import Path
from unittest.mock import Mock

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
def test_fs_Copier_go(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    fs.Copier(target_dir=dstdir, config=config, key_path=["a", "b"]).go()
    assert (dstdir / "foo").is_file()
    assert (dstdir / "subdir" / "bar").is_file()


def test_fs_Copier_go_config_file_dry_run(assets):
    dstdir, cfgdict, _ = assets
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    fs.Copier(target_dir=dstdir, config=cfgdict, key_path=["a", "b"], dry_run=True).go()
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    iotaa.dryrun(False)


def test_fs_Copier_go_no_targetdir_abspath_pass(assets):
    dstdir, cfgdict, _ = assets
    old = cfgdict["a"]["b"]
    cfgdict = {str(dstdir / "foo"): old["foo"], str(dstdir / "bar"): old["subdir/bar"]}
    assets = fs.Copier(config=cfgdict).go()
    assert all(asset.ready() for asset in assets)  # type: ignore


def test_Copier_no_targetdir_relpath_fail(assets):
    _, cfgdict, _ = assets
    with raises(UWConfigError) as e:
        fs.Copier(config=cfgdict, key_path=["a", "b"]).go()
    errmsg = "Relative path '%s' requires the target directory to be specified"
    assert errmsg % "foo" in str(e.value)


def test_fs_Copier__simple():
    assert fs.Copier._simple("relative/path") == Path("relative/path")
    assert fs.Copier._simple("/absolute/path") == Path("/absolute/path")
    assert fs.Copier._simple("file:///absolute/path") == Path("/absolute/path")
    assert fs.Copier._simple("") == Path("")


@mark.parametrize("source", ("dict", "file"))
def test_fs_FilerStager(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    assert fs.FileStager(target_dir=dstdir, config=config, key_path=["a", "b"])


@mark.parametrize("source", ("dict", "file"))
def test_fs_Linker(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    fs.Linker(target_dir=dstdir, config=config, key_path=["a", "b"]).go()
    assert (dstdir / "foo").is_symlink()
    assert (dstdir / "subdir" / "bar").is_symlink()


@mark.parametrize(
    "path,target_dir,msg,fail_expected",
    [
        (
            "/other/path",
            "/some/path",
            "Path '%s' must be relative when target directory is specified",
            True,
        ),
        (
            "foo://bucket/a/b",
            None,
            "Non-filesystem destination path '%s' not currently supported",
            True,
        ),
        (
            "relpath",
            None,
            "Relative path '%s' requires target directory to be specified",
            True,
        ),
        (
            "file://foo.com/a/b",
            "/some/path",
            "Non-filesystem path '%s' invalid when target directory is specified",
            True,
        ),
        ("other/path", "/some/path", None, False),
        ("other/path", "file:///some/path", None, False),
    ],
)
def test_fs_Stager__check_destination_paths_fail(path, target_dir, msg, fail_expected):
    obj = Mock(_dst_paths=[path], _target_dir=target_dir)
    if fail_expected:
        with raises(UWConfigError) as e:
            fs.Stager._check_destination_paths(obj)
        assert str(e.value) == msg % path


@mark.parametrize(
    "path,fail_expected",
    [("foo://bucket/a/b", True), ("/some/path", False), ("file:///some/path", False)],
)
def test_fs_Stager__check_target_dir_fail_bad_scheme(path, fail_expected):
    obj = Mock(_target_dir="foo://bucket/a/b")
    if fail_expected:
        with raises(UWConfigError) as e:
            fs.Stager._check_target_dir(obj)
        assert str(e.value) == "Non-filesystem path '%s' invalid as target directory" % path


@mark.parametrize("source", ("dict", "file"))
def test_fs_Stager__config_block_fail_bad_key_path(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    with raises(UWConfigError) as e:
        ConcreteStager(target_dir=dstdir, config=config, key_path=["a", "x"])
    assert str(e.value) == "Bad config path: a.x"


@mark.parametrize("val", [None, True, False, "str", 42, 3.14, [], tuple()])
def test_fs_Stager__config_block_fails_bad_type(assets, val):
    dstdir, cfgdict, _ = assets
    cfgdict["a"]["b"] = val
    with raises(UWConfigError) as e:
        ConcreteStager(target_dir=dstdir, config=cfgdict, key_path=["a", "b"])
    assert str(e.value) == "Value at a.b must be a dictionary"
