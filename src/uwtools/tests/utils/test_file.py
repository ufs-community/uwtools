"""
Tests for uwtools.utils.file module.
"""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from pytest import fixture, mark, raises

from uwtools.strings import FORMAT
from uwtools.utils import file


@fixture
def assets(tmp_path, utc):
    rundir = tmp_path / "rundir"
    rundir.mkdir()
    assert rundir.is_dir()
    now = utc(2023, 6, 29, 23, 48, 11)
    renamed = rundir.parent / ("rundir_%s" % now.strftime("%Y%m%d_%H%M%S"))
    assert not renamed.is_dir()
    return now, renamed, rundir


def test_StdinProxy():
    msg = "proxying stdin"
    with StringIO(msg) as sio, patch.object(sys, "stdin", new=sio):
        assert sys.stdin.read() == msg
        # Reading from stdin a second time yields no input, as the stream has been exhausted:
        assert sys.stdin.read() == ""
    with StringIO(msg) as sio, patch.object(sys, "stdin", new=sio):
        sp = file.StdinProxy()
        assert sp.read() == msg
        # But the stdin proxy can be read multiple times:
        assert sp.read() == msg
        # And the proxy can be iterated over:
        for line in sp:
            assert line == msg


def test__stdinproxy():
    file._stdinproxy.cache_clear()
    msg0 = "hello world"
    msg1 = "bonjour monde"
    # Unsurprisingly, the first read from stdin finds the expected message:
    with StringIO(msg0) as sio, patch.object(sys, "stdin", new=sio):
        assert file._stdinproxy().read() == msg0
    # But after re-patching stdin with a new message, a second read returns the old message:
    with StringIO(msg1) as sio, patch.object(sys, "stdin", new=sio):
        assert file._stdinproxy().read() == msg0  # <-- the OLD message
    # However, if the cache is cleared, the second message is then read:
    file._stdinproxy.cache_clear()
    with StringIO(msg1) as sio, patch.object(sys, "stdin", new=sio):
        assert file._stdinproxy().read() == msg1  # <-- the NEW message


@mark.parametrize(
    ("ext", "file_type"),
    {
        "atparse": "atparse",
        "bash": "sh",
        "cfg": "ini",
        "fieldtable": "fieldtable",
        "ini": "ini",
        "jinja2": "jinja2",
        "nml": "nml",
        "sh": "sh",
        "yaml": "yaml",
        "yml": "yaml",
    }.items(),
)
def test_get_config_format(ext, file_type):
    assert file.get_config_format(Path(f"a.{ext}")) == file_type


def test_get_config_format_unrecognized():
    assert file.get_config_format(Path("a.jpg")) == FORMAT.yaml


def test_path_if_it_exists(tmp_path):
    # Test non-existent path:
    path = tmp_path / "foo"
    with raises(FileNotFoundError):
        file.path_if_it_exists(str(path))
    # Test directory that exists:
    assert file.path_if_it_exists(str(tmp_path)) == str(tmp_path)
    # Test file that exists:
    path.touch()
    assert file.path_if_it_exists(str(path)) == str(path)


def test_readable_file(tmp_path):
    apath = tmp_path / "afile"
    apath.write_text("hello")
    with file.readable(filepath=apath) as f:
        assert f.read() == "hello"


def test_readable_nofile():
    file._stdinproxy.cache_clear()
    with StringIO("hello") as sio, patch.object(sys, "stdin", new=sio), file.readable() as f:
        assert f.read() == "hello"


def test_resource_path():
    assert file.resource_path().is_dir()


@mark.parametrize("val", [Path("/some/path"), {"foo": 42}])
def test_str2path_passthrough(val):
    assert file.str2path(val) == val


def test_str2path_convert():
    val = "/some/path"
    result = file.str2path(val)
    assert isinstance(result, Path)
    assert result == Path(val)


def test_writable_file(tmp_path):
    apath = tmp_path / "afile"
    with file.writable(filepath=apath) as f:
        assert f.write("hello")
    assert apath.read_text() == "hello"


def test_writable_nofile():
    with file.writable() as f:
        assert f is sys.stdout
