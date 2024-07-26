# pylint: disable=missing-class-docstring,missing-function-docstring
"""
Tests for uwtools.drivers.support module.
"""
from pathlib import Path
from typing import Optional

from iotaa import asset, external, task, tasks

from uwtools.drivers import support
from uwtools.drivers.driver import DriverTimeInvariant


def test_graph():
    @external
    def ready():
        yield "ready"
        yield asset("ready", lambda: True)

    ready()
    assert support.graph().startswith("digraph")

    class SomeDriver(DriverTimeInvariant):
        def provisioned_rundir(self):
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

        def _validate(self, schema_file: Optional[Path] = None):
            pass

    assert support.tasks(SomeDriver) == {
        "run": "A run.",
        "runscript": "The runscript.",
        "t1": "@external t1",
        "t2": "@task t2",
        "t3": "@tasks t3",
        "validate": "Validate the UW driver config.",
    }
