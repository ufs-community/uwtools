"""
API access to the ``uwtools`` ``esg_grid`` driver.
"""

from uwtools.drivers.esg_grid import ESGGrid
from uwtools.drivers.support import graph
from uwtools.utils.api import make_execute as _make_execute
from uwtools.utils.api import make_tasks as _make_tasks

_driver = ESGGrid
execute = _make_execute(_driver)
tasks = _make_tasks(_driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
