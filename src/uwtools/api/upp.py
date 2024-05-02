"""
API access to the ``uwtools`` ``upp`` driver.
"""

from uwtools.drivers.support import graph
from uwtools.drivers.upp import UPP as _Driver
from uwtools.utils.api import make_execute as _make_execute
from uwtools.utils.api import make_tasks as _make_tasks

execute = _make_execute(_Driver, with_cycle=True, with_leadtime=True)
tasks = _make_tasks(_Driver)
__all__ = ["execute", "graph", "tasks"]
