# pylint: disable=missing-function-docstring

import datetime as dt
from unittest.mock import patch

from uwtools.api import ungrib


def test_execute(tmp_path):
    dot = tmp_path / "graph.dot"
    args: dict = {
        "config_file": "config.yaml",
        "cycle": dt.datetime.utcnow(),
        "batch": False,
        "dry_run": True,
        "graph_file": dot,
    }
    with patch.object(ungrib, "Ungrib") as Ungrib:
        assert ungrib.execute(**args, task="foo") is True
    del args["graph_file"]
    Ungrib.assert_called_once_with(**args)
    Ungrib().foo.assert_called_once_with()


def test_graph():
    with patch.object(ungrib.support, "graph") as graph:
        ungrib.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(ungrib.support, "tasks") as _tasks:
        ungrib.tasks()
    _tasks.assert_called_once_with(ungrib.Ungrib)
