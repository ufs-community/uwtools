"""
API access to the ``uwtools`` ``schism`` driver.
"""

from functools import partial

from uwtools.drivers.schism import SCHISM
from uwtools.drivers.support import graph, tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = SCHISM
execute = _make_execute(_driver, with_cycle=True)
tasks = partial(tasks, _driver)
__all__ = ["SCHISM", "execute", "graph", "tasks"]
