# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import datetime as dt
from pathlib import Path
from unittest.mock import patch

from pytest import fixture, raises

from uwtools.api import mpas
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
    with patch.object(mpas, "_MPAS") as MPAS:
        assert mpas.execute(**kwargs, task="foo", graph_file=tmp_path / "graph.dot") is True
    MPAS.assert_called_once_with(**{**kwargs, "config": Path(kwargs["config"])})
    MPAS().foo.assert_called_once_with()


def test_execute_stdin_not_ok(kwargs):
    kwargs["config"] = None
    with raises(UWError) as e:
        mpas.execute(**kwargs, task="foo")
    assert str(e.value) == "Set stdin_ok=True to enable read from stdin"


def test_graph():
    with patch.object(mpas._support, "graph") as graph:
        mpas.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(mpas._support, "tasks") as _tasks:
        mpas.tasks()
    _tasks.assert_called_once_with(mpas._MPAS)
