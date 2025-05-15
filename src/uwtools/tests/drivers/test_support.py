"""
Tests for uwtools.drivers.support module.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import iotaa

from uwtools.drivers import support
from uwtools.drivers.driver import DriverTimeInvariant

if TYPE_CHECKING:
    from pathlib import Path


def test_set_driver_docstring():
    class Parent:
        """
        This will be discarded.

        body
        """

    class Child(Parent):
        """
        head.
        """

    support.set_driver_docstring(Child)
    assert Child.__doc__ is not None
    assert Child.__doc__.startswith("head.\n\n")
    assert Child.__doc__.endswith("body")


def test_tasks():
    class SomeDriver(DriverTimeInvariant):
        @classmethod
        def driver_name(cls):
            pass

        def provisioned_rundir(self):
            pass

        def taskname(self, suffix=None):
            pass

        @iotaa.external
        def t1(self):
            """@external t1."""

        @iotaa.task
        def t2(self):
            """@task t2."""

        @iotaa.tasks
        def t3(self):
            """@tasks t3."""

        @property
        def _resources(self):
            pass

        def _validate(self, schema_file: Path | None = None):
            pass

    assert support.tasks(SomeDriver) == {
        "run": "A run.",
        "runscript": "The runscript.",
        "show_output": "Show the output to be created by this component.",
        "t1": "@external t1.",
        "t2": "@task t2.",
        "t3": "@tasks t3.",
        "validate": "Validate the UW driver config.",
    }
