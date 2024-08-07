"""
API access to the ``uwtools`` ``esg_grid`` driver.
"""

from functools import partial

from uwtools.drivers.esg_grid import ESGGrid
from uwtools.drivers.support import graph, tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = ESGGrid
execute = _make_execute(_driver)
tasks = partial(tasks, _driver)
__all__ = ["ESGGrid", "execute", "graph", "tasks"]
