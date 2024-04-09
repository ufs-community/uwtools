# pylint: disable=missing-class-docstring,missing-function-docstring
"""
Tests for uwtools.drivers.support module.
"""
from iotaa import asset, external, task, tasks

from uwtools.drivers import support
from uwtools.drivers.driver import Driver


def test_graph():
    @external
    def ready():
        yield "ready"
        yield asset("ready", lambda: True)

    ready()
    assert support.graph().startswith("digraph")


def test_tasks():
    class SomeDriver(Driver):
        def provisioned_run_directory(self):
            pass

        @external
        def t1(self):
            "@external t1"

        @task
        def t2(self):
            "@task t2"

        @tasks
        def t3(self):
            "@tasks t3"

        @property
        def _driver_config(self):
            pass

        @property
        def _driver_name(self):
            pass

        @property
        def _resources(self):
            pass

        def _taskname(self, suffix):
            pass

        def _validate(self):
            pass

    assert support.tasks(SomeDriver) == {
        "run": "A run.",
        "t2": "@task t2",
        "t3": "@tasks t3",
        "t1": "@external t1",
        "validate": "Validate driver config.",
    }
