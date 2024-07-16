"""
API access to the ``uwtools`` ``chgres_cube`` driver.
"""

from functools import partial

from uwtools.drivers.chgres_cube import ChgresCube
from uwtools.drivers.support import graph, tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = ChgresCube
execute = _make_execute(_driver, with_cycle=True)
tasks = partial(tasks, _driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
