"""
API access to the ``uwtools`` ``fv3`` driver.
"""

from functools import partial

from uwtools.drivers.fv3 import FV3
from uwtools.drivers.support import graph, tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = FV3
execute = _make_execute(_driver, with_cycle=True)
tasks = partial(tasks, _driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
