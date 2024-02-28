# pylint: disable=missing-function-docstring

import datetime as dt
from unittest.mock import patch

from iotaa import asset, external, task, tasks

from uwtools.api import fv3


def test_execute(tmp_path):
    dot = tmp_path / "graph.dot"
    args: dict = {
        "config_file": "config.yaml",
        "cycle": dt.datetime.utcnow(),
        "batch": False,
        "dry_run": True,
        "graph_file": dot,
    }
    with patch.object(fv3, "FV3") as FV3:
        assert fv3.execute(**args, task="foo") is True
    del args["graph_file"]
    FV3.assert_called_once_with(**args)
    FV3().foo.assert_called_once_with()


def test_graph():
    @external
    def ready():
        yield "ready"
        yield asset("ready", lambda: True)

    ready()
    assert fv3.graph().startswith("digraph")


def test_tasks():
    @external
    def t1():
        "@external t1"

    @task
    def t2():
        "@task t2"

    @tasks
    def t3():
        "@tasks t3"

    with patch.object(fv3, "FV3") as FV3:
        FV3.t1 = t1
        FV3.t2 = t2
        FV3.t3 = t3
        assert fv3.tasks() == {"t2": "@task t2", "t3": "@tasks t3", "t1": "@external t1"}
