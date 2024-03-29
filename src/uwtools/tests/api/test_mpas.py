# pylint: disable=missing-function-docstring,protected-access

import datetime as dt
from unittest.mock import patch

from uwtools.api import mpas


def test_execute(tmp_path):
    cycle = dt.datetime.utcnow()
    dot = tmp_path / "graph.dot"
    args: dict = {
        "batch": False,
        "config": "config.yaml",
        "cycle": cycle,
        "dry_run": True,
        "graph_file": dot,
    }
    with patch.object(mpas, "_MPAS") as MPAS:
        assert mpas.execute(**args, task="foo") is True
    del args["graph_file"]
    MPAS.assert_called_once_with(**args)
    MPAS().foo.assert_called_once_with()


def test_graph():
    with patch.object(mpas._support, "graph") as graph:
        mpas.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(mpas._support, "tasks") as _tasks:
        mpas.tasks()
    _tasks.assert_called_once_with(mpas._MPAS)
