# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.utils.file module.
"""

import sys
from datetime import datetime as dt
from unittest.mock import patch

import pytest
from pytest import fixture, raises

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


@pytest.mark.parametrize("exc", [FileExistsError, RuntimeError])
def test_handle_existing_delete_failure(exc, assets):
    _, _, rundir = assets
    with patch.object(file.shutil, "rmtree", side_effect=exc):
        with raises(RuntimeError) as e:
            file.handle_existing(directory=rundir, action="delete")
        assert "Could not delete directory" in str(e.value)
    assert rundir.is_dir()


def test_handle_existing_delete_success(assets):
    _, _, rundir = assets
    file.handle_existing(directory=rundir, action="delete")
    assert not rundir.is_dir()


@pytest.mark.parametrize("exc", [FileExistsError, RuntimeError])
def test_handle_existing_rename_failure(exc, assets):
    _, renamed, rundir = assets
    with patch.object(file.shutil, "move", side_effect=exc):
        with raises(RuntimeError) as e:
            file.handle_existing(directory=rundir, action="rename")
        assert "Could not rename directory" in str(e.value)
    assert not renamed.is_dir()
    assert rundir.is_dir()


def test_handle_existing_rename_success(assets):
    now, renamed, rundir = assets
    with patch.object(file, "dt") as dt:
        dt.now.return_value = now
        file.handle_existing(directory=rundir, action="rename")
    assert renamed.is_dir()
    assert not rundir.is_dir()


def test_readable_file(tmp_path):
    apath = tmp_path / "afile"
    with open(apath, "w", encoding="utf-8") as f:
        f.write("hello")
    with file.readable(filepath=apath) as f:
        assert f.read() == "hello"


def test_readable_nofile():
    with file.readable() as f:
        assert f is sys.stdin


def test_writable_file(tmp_path):
    apath = tmp_path / "afile"
    with file.writable(filepath=apath) as f:
        assert f.write("hello")
    with open(apath, "r", encoding="utf-8") as f:
        assert f.read() == "hello"


def test_writable_nofile():
    with file.writable() as f:
        assert f is sys.stdout
