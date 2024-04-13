# pylint: disable=missing-function-docstring,protected-access

import datetime as dt
from pathlib import Path
from unittest.mock import patch

from uwtools.api import mpas


def test_execute(tmp_path):
    cycle = dt.datetime.now()
    dot = tmp_path / "graph.dot"
    kwargs: dict = {
        "batch": False,
        "config": "config.yaml",
        "cycle": cycle,
        "dry_run": True,
        "graph_file": dot,
    }
    with patch.object(mpas, "_MPAS") as MPAS:
        assert mpas.execute(**kwargs, task="foo") is True
    del kwargs["graph_file"]
    MPAS.assert_called_once_with(**{**kwargs, "config": Path(kwargs["config"])})
    MPAS().foo.assert_called_once_with()


def test_graph():
    with patch.object(mpas._support, "graph") as graph:
        mpas.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(mpas._support, "tasks") as _tasks:
        mpas.tasks()
    _tasks.assert_called_once_with(mpas._MPAS)
