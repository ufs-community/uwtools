"""
API access to the ``uwtools`` ``ungrib`` driver.
"""

from uwtools.drivers.support import graph
from uwtools.drivers.support import tasks as _tasks
from uwtools.drivers.ungrib import Ungrib
from uwtools.utils.api import make_execute as _make_execute

_driver = Ungrib
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


__all__ = ["Ungrib", "execute", "graph", "schema", "tasks"]
