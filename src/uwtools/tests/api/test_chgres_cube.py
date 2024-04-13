# pylint: disable=missing-function-docstring,protected-access

import datetime as dt
from pathlib import Path
from unittest.mock import patch

import iotaa

from uwtools.api import chgres_cube


def test_execute(tmp_path):
    dot = tmp_path / "graph.dot"
    kwargs: dict = {
        "batch": False,
        "config": "config.yaml",
        "cycle": dt.datetime.now(),
        "dry_run": True,
        "graph_file": dot,
    }
    with patch.object(chgres_cube, "_ChgresCube") as ChgresCube:
        assert chgres_cube.execute(**kwargs, task="foo") is True
    del kwargs["graph_file"]
    ChgresCube.assert_called_once_with(**{**kwargs, "config": Path(kwargs["config"])})
    ChgresCube().foo.assert_called_once_with()


def test_graph():
    with patch.object(iotaa, "graph") as graph:
        chgres_cube.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(chgres_cube._support, "tasks") as _tasks:
        chgres_cube.tasks()
    _tasks.assert_called_once_with(chgres_cube._ChgresCube)
