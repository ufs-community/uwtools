"""
API access to the ``uwtools`` ``orog`` driver.
"""

from functools import partial

from uwtools.drivers.orog import Orog
from uwtools.drivers.support import graph, tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = Orog
execute = _make_execute(_driver)
tasks = partial(tasks, _driver)
__all__ = ["Orog", "execute", "graph", "tasks"]
