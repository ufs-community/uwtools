# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for uwtools.utils.file module.
"""

import sys
from datetime import datetime as dt
from io import StringIO
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools.exceptions import UWError
from uwtools.types import ExistAct
from uwtools.utils import file


@fixture
def assets(tmp_path):
    rundir = tmp_path / "rundir"
    rundir.mkdir()
    assert rundir.is_dir()
    now = dt(2023, 6, 29, 23, 48, 11)
    renamed = rundir.parent / ("rundir_%s" % now.strftime("%Y%m%d_%H%M%S"))
    assert not renamed.is_dir()
    return now, renamed, rundir


def test_StdinProxy():
    msg = "proxying stdin"
    with patch.object(sys, "stdin", new=StringIO(msg)):
        assert sys.stdin.read() == msg
        # Reading from stdin a second time yields no input, as the stream has been exhausted:
        assert sys.stdin.read() == ""
    with patch.object(sys, "stdin", new=StringIO(msg)):
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
    with patch.object(sys, "stdin", new=StringIO(msg0)):
        assert file._stdinproxy().read() == msg0
    # But after re-patching stdin with a new message, a second read returns the old message:
    with patch.object(sys, "stdin", new=StringIO(msg1)):
        assert file._stdinproxy().read() == msg0  # <-- the OLD message
    # However, if the cache is cleared, the second message is then read:
    file._stdinproxy.cache_clear()
    with patch.object(sys, "stdin", new=StringIO(msg1)):
        assert file._stdinproxy().read() == msg1  # <-- the NEW message


def test_get_file_format():
    for ext, file_type in {
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
    }.items():
        assert file.get_file_format(f"a.{ext}") == file_type


def test_get_file_format_unrecognized():
    with raises(UWError):
        file.get_file_format("a.jpg")


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
    with open(apath, "w", encoding="utf-8") as f:
        f.write("hello")
    with file.readable(filepath=apath) as f:
        assert f.read() == "hello"


def test_readable_nofile():
    with file.readable() as f:
        assert hasattr(f, "read")


def test_resource_pathobj():
    assert file.resource_pathobj().is_dir()


def test_validate_existing_action_fail():
    with raises(ValueError):
        file.validate_existing_action(ExistAct.quit, [ExistAct.delete])


def test_validate_existing_action_pass():
    file.validate_existing_action(ExistAct.quit, [ExistAct.delete, ExistAct.quit])


def test_writable_file(tmp_path):
    apath = tmp_path / "afile"
    with file.writable(filepath=apath) as f:
        assert f.write("hello")
    with open(apath, "r", encoding="utf-8") as f:
        assert f.read() == "hello"


def test_writable_nofile():
    with file.writable() as f:
        assert f is sys.stdout
