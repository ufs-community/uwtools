# pylint: disable=missing-function-docstring,redefined-outer-name
"""
Tests for uwtools.utils.file_helpers module.
"""
from datetime import datetime as dt
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools.utils import file_helpers


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
    with patch.object(file_helpers.shutil, "rmtree", side_effect=exc):
        with raises(RuntimeError) as e:
            file_helpers.handle_existing(run_directory=rundir, exist_act="delete")
        assert "Could not delete directory" in str(e.value)
    assert rundir.is_dir()


def test_handle_existing_delete_success(assets):
    _, _, rundir = assets
    file_helpers.handle_existing(run_directory=rundir, exist_act="delete")
    assert not rundir.is_dir()


@pytest.mark.parametrize("exc", [FileExistsError, RuntimeError])
def test_handle_existing_rename_failure(exc, assets):
    _, renamed, rundir = assets
    with patch.object(file_helpers.shutil, "move", side_effect=exc):
        with raises(RuntimeError) as e:
            file_helpers.handle_existing(run_directory=rundir, exist_act="rename")
        assert "Could not rename directory" in str(e.value)
    assert not renamed.is_dir()
    assert rundir.is_dir()


def test_handle_existing_rename_success(assets):
    now, renamed, rundir = assets
    with patch.object(file_helpers, "dt") as dt:
        dt.now.return_value = now
        file_helpers.handle_existing(run_directory=rundir, exist_act="rename")
    assert renamed.is_dir()
    assert not rundir.is_dir()
