# pylint: disable=missing-function-docstring,protected-access

import datetime as dt
from unittest.mock import patch

import iotaa

from uwtools.api import chgres_cube


def test_execute(tmp_path):
    dot = tmp_path / "graph.dot"
    args: dict = {
        "config_file": "config.yaml",
        "cycle": dt.datetime.utcnow(),
        "batch": False,
        "dry_run": True,
        "graph_file": dot,
    }
    with patch.object(chgres_cube, "_ChgresCube") as ChgresCube:
        assert chgres_cube.execute(**args, task="foo") is True
    del args["graph_file"]
    ChgresCube.assert_called_once_with(**args)
    ChgresCube().foo.assert_called_once_with()


def test_graph():
    with patch.object(iotaa, "graph") as graph:
        chgres_cube.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(chgres_cube.support, "tasks") as _tasks:
        chgres_cube.tasks()
    _tasks.assert_called_once_with(chgres_cube._ChgresCube)
