# pylint: disable=missing-function-docstring,protected-access

from pathlib import Path
from unittest.mock import patch

import iotaa

from uwtools.api import esg_grid


def test_execute(tmp_path):
    dot = tmp_path / "graph.dot"
    args: dict = {
        "config": Path("config.yaml"),
        "batch": False,
        "dry_run": True,
        "graph_file": dot,
    }
    with patch.object(esg_grid, "_EsgGrid") as EsgGrid:
        assert esg_grid.execute(**args, task="foo") is True
    del args["graph_file"]
    EsgGrid.assert_called_once_with(**args)
    EsgGrid().foo.assert_called_once_with()


def test_graph():
    with patch.object(iotaa, "graph") as graph:
        esg_grid.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(esg_grid._support, "tasks") as _tasks:
        esg_grid.tasks()
    _tasks.assert_called_once_with(esg_grid._EsgGrid)
