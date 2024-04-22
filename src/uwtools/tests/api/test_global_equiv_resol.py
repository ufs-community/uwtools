# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import datetime as dt
from pathlib import Path
from unittest.mock import patch

from pytest import fixture

from uwtools.api import global_equiv_resol


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
    with patch.object(global_equiv_resol, "_GlobalEquivResol") as GlobalEquivResol:
        assert global_equiv_resol.execute(**kwargs, task="foo", graph_file=tmp_path / "graph.dot") is True
    GlobalEquivResol.assert_called_once_with(**{**kwargs, "config": Path(kwargs["config"])})
    GlobalEquivResol().foo.assert_called_once_with()


def test_graph():
    with patch.object(global_equiv_resol._support, "graph") as graph:
        global_equiv_resol.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(global_equiv_resol._support, "tasks") as _tasks:
        global_equiv_resol.tasks()
    _tasks.assert_called_once_with(global_equiv_resol._GlobalEquivResol)
