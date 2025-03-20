# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=protected-access
# pylint: disable=redefined-outer-name

import logging
from logging import getLogger
from pathlib import Path
from textwrap import dedent
from unittest.mock import Mock, patch

import iotaa
import yaml
from pytest import fixture, mark, raises

from uwtools import fs
from uwtools.config.support import uw_yaml_loader
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.tests.support import logged
from uwtools.utils import tasks

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


@fixture
def _expand_glob_assets(tmp_path):
    src, dst = [tmp_path / x for x in ("src", "dst")]
    src.mkdir()
    f, d = [src / x for x in ("file", "directory")]
    f.touch()
    d.mkdir()
    config = f"""
    {dst}/<f>: !glob {src}/*
    """
    return dst, f, d, config


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


@iotaa.external
def exists(*_args, **_kwargs):
    yield "exists"
    yield iotaa.asset(None, lambda: True)


# Tests


@mark.parametrize("src_func", [str, Path])
@mark.parametrize("dst_func", [str, Path])
@mark.parametrize("tgt_func", [str, Path])
def test_fs_Copier_go(src_func, dst_func, tgt_func):
    src, dst, tgt = src_func("/src/file"), dst_func("file"), tgt_func("/dst")
    obj = Mock(_simple=fs.Copier._simple, _target_dir=tgt)
    obj._expand_glob.return_value = [(dst, src)]
    with patch.object(fs, "filecopy") as filecopy:
        filecopy.return_value = iotaa.NodeExternal(
            taskname="test", threads=0, logger=getLogger(), assets_=None
        )
        fs.Copier.go(obj)
    filecopy.assert_called_once_with(src=src, dst=Path("/dst/file"))


@mark.parametrize("source", ("dict", "file"))
def test_fs_Copier_go_live(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    fs.Copier(target_dir=dstdir, config=config, key_path=["a", "b"]).go()
    assert (dstdir / "foo").is_file()
    assert (dstdir / "subdir" / "bar").is_file()


def test_fs_Copier_go_live_config_file_dry_run(assets):
    dstdir, cfgdict, _ = assets
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    copier = fs.Copier(target_dir=dstdir, config=cfgdict, key_path=["a", "b"])
    copier.go(dry_run=True)
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()


def test_fs_Copier_go_live_no_targetdir_abspath_pass(assets):
    dstdir, cfgdict, _ = assets
    old = cfgdict["a"]["b"]
    cfgdict = {str(dstdir / "foo"): old["foo"], str(dstdir / "bar"): old["subdir/bar"]}
    fs.Copier(config=cfgdict).go()
    assert all(path.is_file() for path in [dstdir / "foo", dstdir / "bar"])


def test_Copier_go_no_targetdir_relpath_fail(assets):
    _, cfgdict, _ = assets
    with raises(UWConfigError) as e:
        fs.Copier(config=cfgdict, key_path=["a", "b"]).go()
    errmsg = "Relative path '%s' requires target directory to be specified"
    assert errmsg % "foo" in str(e.value)


def test_Copier__expand_glob(_expand_glob_assets):
    dst, f, _, config = _expand_glob_assets
    fs.Copier(config=yaml.load(dedent(config), Loader=uw_yaml_loader())).go()
    # Only file is copied, not directory:
    assert list(dst.glob("*")) == [dst / f.name]


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


def test_fs_FileStager__expand_glob(caplog, tmp_path):
    log.setLevel(logging.WARNING)
    d = tmp_path
    # Files matching the pattern to include:
    for x in ["a1", "a2", "b1"]:
        (d / x).touch()
    # A subdirectory matching the pattern to ignore:
    (d / "a3").mkdir()
    # Subdirectories, with both files to include and to ignore:
    for x in ["d1", "d2"]:
        (d / x).mkdir()
        (d / x / "a3").touch()
        (d / x / "b1").touch()
    # Proceed:
    config = f"""
    /dst/<a>: !glob {d}/**/a*
    /dst/b1: {d}/b1
    """
    obj = Mock(_config=yaml.load(dedent(config), Loader=uw_yaml_loader()))
    assert sorted(fs.FileStager._expand_glob(obj)) == [
        ("/dst/a1", str(d / "a1")),
        ("/dst/a2", str(d / "a2")),
        ("/dst/b1", str(d / "b1")),
        ("/dst/d1/a3", str(d / "d1" / "a3")),
        ("/dst/d2/a3", str(d / "d2" / "a3")),
    ]
    assert logged(caplog, f"Ignoring directory {d}/a3")


def test_fs_FileStager__expand_glob_bad_scheme(caplog):
    config = """
    /dst/<a>: !glob https://foo.com/obj/*
    """
    obj = Mock(_config=yaml.load(dedent(config), Loader=uw_yaml_loader()))
    assert not fs.FileStager._expand_glob(obj)
    msg = "URL scheme 'https' incompatible with tag !glob in: !glob https://foo.com/obj/*"
    assert logged(caplog, msg)


def test_fs_FileStager__expand_glob_file_scheme():
    config = """
    /dst/<a>: !glob file:///src/a*
    """
    obj = Mock(_config=yaml.load(dedent(config), Loader=uw_yaml_loader()))
    with patch.object(fs, "iglob", return_value=["/src/a1", "/src/a2"]) as iglob:
        assert fs.FileStager._expand_glob(obj) == [
            ("/dst/a1", "/src/a1"),
            ("/dst/a2", "/src/a2"),
        ]
    iglob.assert_called_once_with("/src/a*", recursive=True)


@mark.parametrize("source", ("dict", "file"))
def test_fs_Linker(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    fs.Linker(target_dir=dstdir, config=config, key_path=["a", "b"]).go()
    assert (dstdir / "foo").is_symlink()
    assert (dstdir / "subdir" / "bar").is_symlink()


def test_Linker__expand_glob(_expand_glob_assets):
    dst, f, d, config = _expand_glob_assets
    fs.Linker(config=yaml.load(dedent(config), Loader=uw_yaml_loader())).go()
    # Both file and directory are linked:
    assert set(dst.glob("*")) == set([dst / f.name, dst / d.name])


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


@mark.parametrize(
    ["dst_in", "dst_out"],
    [("/path/to/dst", "/path/to/dst"), ("file:///path/to/dst", "/path/to/dst")],
)
def test_fs_filecopy_hsi(dst_in, dst_out):
    src = "hsi://path/to/file"
    with patch.object(tasks, "_filecopy_hsi") as _filecopy_hsi, patch.object(
        tasks, "existing", exists
    ):
        fs.filecopy(src=src, dst=dst_in)
    _filecopy_hsi.assert_called_once_with(src, Path(dst_out))


@mark.parametrize("scheme", ["http", "https"])
@mark.parametrize(
    ["dst_in", "dst_out"],
    [("/path/to/dst", "/path/to/dst"), ("file:///path/to/dst", "/path/to/dst")],
)
def test_fs_filecopy_http(scheme, dst_in, dst_out):
    src = f"{scheme}://a.com/file"
    with patch.object(tasks, "_filecopy_http") as _filecopy_http, patch.object(
        tasks, "existing", exists
    ):
        fs.filecopy(src=src, dst=dst_in)
    _filecopy_http.assert_called_once_with(src, Path(dst_out))


@mark.parametrize(
    ["src_in", "src_out"],
    [("/path/to/src", "/path/to/src"), ("file:///path/to/src", "/path/to/src")],
)
@mark.parametrize(
    ["dst_in", "dst_out"],
    [("/path/to/dst", "/path/to/dst"), ("file:///path/to/dst", "/path/to/dst")],
)
def test_fs_filecopy_local(src_in, src_out, dst_in, dst_out):
    with patch.object(tasks, "_filecopy_local") as _filecopy_local, patch.object(
        tasks, "file", exists
    ):
        fs.filecopy(src=src_in, dst=dst_in)
    _filecopy_local.assert_called_once_with(Path(src_out), Path(dst_out))
