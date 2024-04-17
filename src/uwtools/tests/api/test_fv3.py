# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import datetime as dt
from pathlib import Path
from unittest.mock import patch

from pytest import fixture

from uwtools.api import fv3


@fixture
def kwargs():
    return {
        "batch": False,
        "config": "config.yaml",
        "cycle": dt.datetime.now(),
        "dry_run": True,
    }


def test_execute(kwargs, tmp_path):
    with patch.object(fv3, "_FV3") as FV3:
        assert fv3.execute(**kwargs, task="foo", graph_file=tmp_path / "graph.dot") is True
    FV3.assert_called_once_with(**{**kwargs, "config": Path(kwargs["config"])})
    FV3().foo.assert_called_once_with()


def test_graph():
    with patch.object(fv3._support, "graph") as graph:
        fv3.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(fv3._support, "tasks") as _tasks:
        fv3.tasks()
    _tasks.assert_called_once_with(fv3._FV3)
