"""
API access to the ``uwtools`` ``upp`` driver.
"""

from functools import partial

from uwtools.drivers.support import graph, tasks
from uwtools.drivers.upp import UPP
from uwtools.utils.api import make_execute as _make_execute

_driver = UPP
execute = _make_execute(_driver, with_cycle=True, with_leadtime=True)
tasks = partial(tasks, _driver)
__all__ = ["UPP", "execute", "graph", "tasks"]
