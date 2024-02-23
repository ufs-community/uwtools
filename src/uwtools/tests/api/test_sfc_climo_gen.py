# pylint: disable=missing-function-docstring

from unittest.mock import patch

from iotaa import asset, external, task, tasks

from uwtools.api import sfc_climo_gen


def test_execute(tmp_path):
    dot = tmp_path / "graph.dot"
    args: dict = {
        "config_file": "config.yaml",
        "batch": False,
        "dry_run": True,
        "graph_file": dot,
    }
    with patch.object(sfc_climo_gen, "SfcClimoGen") as SfcClimoGen:
        assert sfc_climo_gen.execute(**args, task="foo") is True
    del args["graph_file"]
    SfcClimoGen.assert_called_once_with(**args)
    SfcClimoGen().foo.assert_called_once_with()


def test_graph():
    @external
    def ready():
        yield "ready"
        yield asset("ready", lambda: True)

    ready()
    assert sfc_climo_gen.graph().startswith("digraph")


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

    with patch.object(sfc_climo_gen, "SfcClimoGen") as SfcClimoGen:
        SfcClimoGen.t1 = t1
        SfcClimoGen.t2 = t2
        SfcClimoGen.t3 = t3
        assert sfc_climo_gen.tasks() == {"t2": "@task t2", "t3": "@tasks t3", "t1": "@external t1"}
