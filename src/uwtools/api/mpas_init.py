"""
API access to the ``uwtools`` ``mpas_init`` driver.
"""

from functools import partial

from uwtools.drivers.mpas_init import MPASInit
from uwtools.drivers.support import graph, tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = MPASInit
execute = _make_execute(_driver, with_cycle=True)
tasks = partial(tasks, _driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
