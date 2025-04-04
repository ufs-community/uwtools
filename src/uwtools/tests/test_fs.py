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
    cfgfile.write_text(yaml.dump(cfgdict))
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
    obj._expand_glob.return_value = [(dst, src, False)]
    with patch.object(fs, "filecopy") as filecopy:
        filecopy.return_value = iotaa.NodeExternal(
            taskname="test", threads=0, logger=getLogger(), assets_=None
        )
        fs.Copier.go(obj)
    filecopy.assert_called_once_with(src=src, dst=Path("/dst/file"), check=False)


@mark.parametrize("source", ["dict", "file"])
def test_fs_Copier_go__live(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    fs.Copier(target_dir=dstdir, config=config, key_path=["a", "b"]).go()
    assert (dstdir / "foo").is_file()
    assert (dstdir / "subdir" / "bar").is_file()


def test_fs_Copier_go__live_config_file_dry_run(assets):
    dstdir, cfgdict, _ = assets
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()
    copier = fs.Copier(target_dir=dstdir, config=cfgdict, key_path=["a", "b"])
    copier.go(dry_run=True)
    assert not (dstdir / "foo").exists()
    assert not (dstdir / "subdir" / "bar").exists()


def test_fs_Copier_go__live_no_targetdir_abspath_pass(assets):
    dstdir, cfgdict, _ = assets
    old = cfgdict["a"]["b"]
    cfgdict = {str(dstdir / "foo"): old["foo"], str(dstdir / "bar"): old["subdir/bar"]}
    fs.Copier(config=cfgdict).go()
    assert all(path.is_file() for path in [dstdir / "foo", dstdir / "bar"])


def test_Copier_go__no_targetdir_relpath_fail(assets):
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
    assert fs.Copier._simple("") == Path("")  # noqa: PTH201


@mark.parametrize("source", ["dict", "file"])
def test_fs_FilerStager(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    assert fs.FileStager(target_dir=dstdir, config=config, key_path=["a", "b"])


def test_fs_FileStager__expand_glob(tmp_path):
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
    a_files = [
        ("/dst/a1", str(d / "a1"), False),
        ("/dst/a2", str(d / "a2"), False),
        ("/dst/d1/a3", str(d / "d1" / "a3"), False),
        ("/dst/d2/a3", str(d / "d2" / "a3"), False),
    ]
    obj._expand_glob_local.return_value = a_files
    assert set(fs.FileStager._expand_glob(obj)) == {*a_files, ("/dst/b1", str(d / "b1"), True)}


def test_fs_FileStager__expand_glob__bad_scheme(logged):
    config = """
    /dst/<a>: !glob https://foo.com/obj/*
    """
    obj = Mock(_config=yaml.load(dedent(config), Loader=uw_yaml_loader()))
    assert not fs.FileStager._expand_glob(obj)
    msg = "URL scheme 'https' incompatible with tag !glob in: !glob https://foo.com/obj/*"
    assert logged(msg)


@mark.parametrize("prefix", ["", "file://"])
def test_fs_FileStager__expand_glob__file_scheme(prefix):
    config = f"""
    /dst/<a>: !glob {prefix}/src/a*
    """
    obj = Mock(_config=yaml.load(dedent(config), Loader=uw_yaml_loader()))
    obj._expand_glob_local.return_value = []
    fs.FileStager._expand_glob(obj)
    obj._expand_glob_local.assert_called_once_with("/src/a*", "/dst/<a>")


def test_fs_FileStager__expand_glob__hsi_scheme():
    config = """
    /dst/<a>: !glob hsi:///src/a*
    """
    obj = Mock(_config=yaml.load(dedent(config), Loader=uw_yaml_loader()))
    obj._expand_glob_hsi.return_value = []
    fs.FileStager._expand_glob(obj)
    obj._expand_glob_hsi.assert_called_once_with("/src/a*", "/dst/<a>")


def test_fs_FileStager__expand_glob__htar_scheme():
    config = """
    /dst/<a>: !glob htar:///src/a*?f*
    """
    obj = Mock(_config=yaml.load(dedent(config), Loader=uw_yaml_loader()))
    obj._expand_glob_htar.return_value = []
    fs.FileStager._expand_glob(obj)
    obj._expand_glob_htar.assert_called_once_with("/src/a*", "f*", "/dst/<a>")


@mark.parametrize(("matches", "success"), [(True, True), (False, True), (False, False)])
def test_fs_FileStager__expand_glob_hsi(logged, matches, success):
    obj = Mock(wraps=fs.FileStager)
    glob_pattern = "/src/a*"
    output = {
        True: """
        [connecting to hpsscore1.fairmont.rdhpcs.noaa.gov/1217]
        /BMC/rtrr/5year/uwtools/code.tar
        /BMC/rtrr/5year/uwtools/data.tar
        """,
        False: """
        [connecting to hpsscore1.fairmont.rdhpcs.noaa.gov/1217]
        *** Warning: No matching names located for '/BMC/rtrr/5year/uwtools/*.foo'
        """,
    }[matches]
    with patch.object(fs, "run_shell_cmd") as run_shell_cmd:
        run_shell_cmd.return_value = (success, dedent(output).strip())
        result = fs.FileStager._expand_glob_hsi(obj, glob_pattern, "/dst/<a>")
        if success:
            if matches:
                assert result == [
                    (
                        "/dst/BMC/rtrr/5year/uwtools/code.tar",
                        "hsi:///BMC/rtrr/5year/uwtools/code.tar",
                        False,
                    ),
                    (
                        "/dst/BMC/rtrr/5year/uwtools/data.tar",
                        "hsi:///BMC/rtrr/5year/uwtools/data.tar",
                        False,
                    ),
                ]
            else:
                assert not result
                assert logged(
                    "*** Warning: No matching names located for '/BMC/rtrr/5year/uwtools/*.foo'"
                )
        else:
            assert not result
    run_shell_cmd.assert_called_once_with(f"hsi -q ls -1 '{glob_pattern}'")


@mark.parametrize("success", [True, False])
def test_fs_FileStager__expand_glob_htar(success):
    outputs = [
        """
        [connecting to hpsscore1.fairmont.rdhpcs.noaa.gov/1217]
        HTAR: -rw-r--r--  Paul.Madden/rtruc         64 2025-04-04 04:37  a1.c
        HTAR: -rw-r--r--  Paul.Madden/rtruc         22 2025-04-04 04:38  a1.py
        HTAR: -rw-------  Paul.Madden/rtruc        256 2025-04-04 12:58  /tmp/HTAR_CF_CHK_2834605_1743771535
        HTAR: HTAR SUCCESSFUL
        """,  # noqa: E501
        """
        [connecting to hpsscore1.fairmont.rdhpcs.noaa.gov/1217]
        HTAR: -rw-r--r--  Paul.Madden/rtruc          3 2025-03-29 16:47  a1.txt
        HTAR: -rw-r--r--  Paul.Madden/rtruc          3 2025-03-29 16:48  a2.dat
        HTAR: -rw-r--r--  Paul.Madden/rtruc          3 2025-03-29 16:48  b1.txt
        HTAR: -rw-r--r--  Paul.Madden/rtruc          3 2025-03-29 16:48  b2.dat
        HTAR: -rw-------  Paul.Madden/rtruc        256 2025-03-29 17:14  /tmp/HTAR_CF_CHK_4120691_1743268474
        HTAR: HTAR SUCCESSFUL
        """,  # noqa: E501
    ]
    obj = Mock(wraps=fs.FileStager)
    _expand_glob_hsi = Mock(return_value=[(None, f"hsi:///a{n}.tar", None) for n in (1, 2)])
    with (
        patch.object(obj, "_expand_glob_hsi", _expand_glob_hsi),
        patch.object(fs, "run_shell_cmd") as run_shell_cmd,
    ):
        run_shell_cmd.side_effect = [(success, dedent(output).strip()) for output in outputs]
        result = fs.FileStager._expand_glob_htar(obj, "/src/a*", "a1.*", "/dst/<a>")
        if success:
            assert result == [
                ("/dst/a1.c", "htar:///a1.tar?a1.c", False),
                ("/dst/a1.py", "htar:///a1.tar?a1.py", False),
                ("/dst/a1.txt", "htar:///a2.tar?a1.txt", False),
            ]
            actual = [x[0][0] for x in run_shell_cmd.call_args_list]
            expected = [f"htar -qtf '/a{n}.tar'" for n in (1, 2)]
            assert actual == expected
        else:
            assert not result


def test_fs_FileStager__expand_glob_local():
    obj = Mock(wraps=fs.FileStager)
    with patch.object(fs.glob, "iglob", return_value=["/src/a1", "/src/a2"]) as iglob:
        assert fs.FileStager._expand_glob_local(obj, "/src/a*", "/dst/<a>") == [
            ("/dst/a1", "/src/a1", False),
            ("/dst/a2", "/src/a2", False),
        ]
    iglob.assert_called_once_with("/src/a*", recursive=True)


@mark.parametrize(
    "args",
    [
        ("/a/**/c", "/a/b/x/c", "/foo/b/x/c", False),
        ("/a/*/*", "/a/b/c", "/foo/b/c", False),
        ("/a/*/x/*/c", "/a/b/x/y/c", "/foo/b/x/y/c", False),
        ("/a/b/*", "/a/b/c", "/foo/c", False),
        ("/a/b/**/c", "/a/b/c", "/foo/c", False),
        ("/a/b/*/c", "/a/b/x/c", "/foo/x/c", False),
        ("/a/b/c", "/a/b/c", "/foo/c", True),
    ],
)
def test_fs_FileStager__expand_glob_resolve(args):
    glob_pattern, path, dst, nonglob = args
    actual = fs.FileStager._expand_glob_resolve(
        glob_pattern=glob_pattern, path=path, dst="/foo/<f>"
    )
    assert actual == (dst, path, nonglob)


@mark.parametrize("source", ["dict", "file"])
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
    assert set(dst.glob("*")) == {dst / f.name, dst / d.name}


@mark.parametrize(
    ("path", "target_dir", "msg", "fail_expected"),
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
def test_fs_Stager__check_destination_paths__fail(path, target_dir, msg, fail_expected):
    obj = Mock(_dst_paths=[path], _target_dir=target_dir)
    if fail_expected:
        with raises(UWConfigError) as e:
            fs.Stager._check_destination_paths(obj)
        assert str(e.value) == msg % path


@mark.parametrize(
    ("path", "fail_expected"),
    [("foo://bucket/a/b", True), ("/some/path", False), ("file:///some/path", False)],
)
def test_fs_Stager__check_target_dir__fail_bad_scheme(path, fail_expected):
    obj = Mock(_target_dir="foo://bucket/a/b")
    if fail_expected:
        with raises(UWConfigError) as e:
            fs.Stager._check_target_dir(obj)
        assert str(e.value) == "Non-filesystem path '%s' invalid as target directory" % path


@mark.parametrize("source", ["dict", "file"])
def test_fs_Stager__config_block__fail_bad_key_path(assets, source):
    dstdir, cfgdict, cfgfile = assets
    config = cfgdict if source == "dict" else cfgfile
    with raises(UWConfigError) as e:
        ConcreteStager(target_dir=dstdir, config=config, key_path=["a", "x"])
    assert str(e.value) == "Bad config path: a.x"


@mark.parametrize("val", [None, True, False, "str", 42, 3.14, [], tuple()])
def test_fs_Stager__config_block__fail_bad_type(assets, val):
    dstdir, cfgdict, _ = assets
    cfgdict["a"]["b"] = val
    with raises(UWConfigError) as e:
        ConcreteStager(target_dir=dstdir, config=cfgdict, key_path=["a", "b"])
    assert str(e.value) == "Value at a.b must be a dictionary"
