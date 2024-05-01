"""
API access to the ``uwtools`` ``esg_grid`` driver.
"""

from uwtools.drivers.esg_grid import ESGGrid as _Driver
from uwtools.drivers.support import graph
from uwtools.utils.api import make_execute as _make_execute
from uwtools.utils.api import make_tasks as _make_tasks

execute = _make_execute(_Driver, with_cycle=False)
tasks = _make_tasks(_Driver)
__all__ = ["execute", "graph", "tasks"]
