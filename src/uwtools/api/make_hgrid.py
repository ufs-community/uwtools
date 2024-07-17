"""
API access to the ``uwtools`` ``make_hgrid`` driver.
"""

from functools import partial

from uwtools.drivers.make_hgrid import MakeHgrid
from uwtools.drivers.support import graph, tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = MakeHgrid
execute = _make_execute(_driver)
tasks = partial(tasks, _driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
