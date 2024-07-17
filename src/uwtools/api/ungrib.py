"""
API access to the ``uwtools`` ``ungrib`` driver.
"""

from functools import partial

from uwtools.drivers.support import graph, tasks
from uwtools.drivers.ungrib import Ungrib
from uwtools.utils.api import make_execute as _make_execute

_driver = Ungrib
execute = _make_execute(_driver, with_cycle=True)
tasks = partial(tasks, _driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
