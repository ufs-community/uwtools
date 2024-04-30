# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

from pathlib import Path
from unittest.mock import patch

from pytest import fixture

from uwtools.api import make_hgrid


@fixture
def kwargs():
    return {
        "batch": False,
        "config": "config.yaml",
        "dry_run": True,
    }


def test_execute(kwargs, tmp_path):
    with patch.object(make_hgrid, "_MakeHgrid") as MakeHgrid:
        assert make_hgrid.execute(**kwargs, task="foo", graph_file=tmp_path / "graph.dot") is True
    MakeHgrid.assert_called_once_with(**{**kwargs, "config": Path(kwargs["config"])})
    MakeHgrid().foo.assert_called_once_with()


def test_graph():
    with patch.object(make_hgrid._support, "graph") as graph:
        make_hgrid.graph()
    graph.assert_called_once_with()


def test_tasks():
    with patch.object(make_hgrid._support, "tasks") as _tasks:
        make_hgrid.tasks()
