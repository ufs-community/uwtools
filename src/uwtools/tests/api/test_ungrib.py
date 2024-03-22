# pylint: disable=missing-function-docstring,protected-access

import datetime as dt
from unittest.mock import patch

from uwtools.api import ungrib


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
    with patch.object(ungrib, "_Ungrib") as Ungrib:
        assert ungrib.execute(**args, task="foo") is True
    del args["graph_file"]
    Ungrib.assert_called_once_with(**args)
    Ungrib().foo.assert_called_once_with()


def test_graph():
    with patch.object(ungrib._support, "graph") as graph:
        ungrib.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(ungrib._support, "tasks") as _tasks:
        ungrib.tasks()
    _tasks.assert_called_once_with(ungrib._Ungrib)
