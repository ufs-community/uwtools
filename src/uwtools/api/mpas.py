"""
API access to the ``uwtools`` ``mpas`` driver.
"""

from functools import partial

from uwtools.drivers.mpas import MPAS
from uwtools.drivers.support import graph, tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = MPAS
execute = _make_execute(_driver, with_cycle=True)
tasks = partial(tasks, _driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
