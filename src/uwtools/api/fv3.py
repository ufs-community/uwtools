"""
API access to the ``uwtools`` ``fv3`` driver.
"""

from uwtools.drivers.fv3 import FV3
from uwtools.drivers.support import graph
from uwtools.drivers.support import tasks as _tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = FV3
execute = _make_execute(_driver, with_cycle=True)


def schema() -> dict:
    """
    Return the driver's schema.
    """
    return _driver.schema()


def tasks() -> dict[str, str]:
    """
    Return a mapping from task names to their one-line descriptions.
    """
    return _tasks(_driver)


__all__ = ["FV3", "execute", "graph", "schema", "tasks"]
