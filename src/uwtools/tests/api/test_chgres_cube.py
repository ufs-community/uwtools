# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import datetime as dt
from pathlib import Path
from unittest.mock import patch

import iotaa
from pytest import fixture, raises

from uwtools.api import chgres_cube
from uwtools.exceptions import UWError


@fixture
def kwargs():
    return {
        "batch": False,
        "config": "config.yaml",
        "cycle": dt.datetime.now(),
        "dry_run": True,
    }


def test_execute(kwargs, tmp_path):
    dot = tmp_path / "graph.dot"
    with patch.object(chgres_cube, "_ChgresCube") as ChgresCube:
        assert chgres_cube.execute(**kwargs, task="foo", graph_file=dot) is True
    ChgresCube.assert_called_once_with(**{**kwargs, "config": Path(kwargs["config"])})
    ChgresCube().foo.assert_called_once_with()


def test_execute_stdin_not_ok(kwargs):
    kwargs["config"] = None
    with raises(UWError) as e:
        chgres_cube.execute(**kwargs, task="foo")
    assert str(e.value) == "Set stdin_ok=True to enable read from stdin"


def test_graph():
    with patch.object(iotaa, "graph") as graph:
        chgres_cube.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(chgres_cube._support, "tasks") as _tasks:
        chgres_cube.tasks()
    _tasks.assert_called_once_with(chgres_cube._ChgresCube)
