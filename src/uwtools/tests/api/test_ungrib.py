# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import datetime as dt
from pathlib import Path
from unittest.mock import patch

from pytest import fixture, raises

from uwtools.api import ungrib
from uwtools.exceptions import UWError


@fixture
def kwargs():
    cycle = dt.datetime.now()
    return {
        "batch": False,
        "config": "config.yaml",
        "cycle": cycle,
        "dry_run": True,
    }


def test_execute(kwargs, tmp_path):
    with patch.object(ungrib, "_Ungrib") as Ungrib:
        assert ungrib.execute(**kwargs, task="foo", graph_file=tmp_path / "graph.dot") is True
    Ungrib.assert_called_once_with(**{**kwargs, "config": Path(kwargs["config"])})
    Ungrib().foo.assert_called_once_with()


def test_execute_stdin_not_ok(kwargs):
    kwargs["config"] = None
    with raises(UWError) as e:
        ungrib.execute(**kwargs, task="foo")
    assert str(e.value) == "Set stdin_ok=True to enable read from stdin"


def test_graph():
    with patch.object(ungrib._support, "graph") as graph:
        ungrib.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(ungrib._support, "tasks") as _tasks:
        ungrib.tasks()
    _tasks.assert_called_once_with(ungrib._Ungrib)
