"""
API access to the ``uwtools`` ``cdeps`` driver.
"""

from uwtools.drivers.cdeps import CDEPS
from uwtools.drivers.support import graph
from uwtools.utils.api import make_execute as _make_execute
from uwtools.utils.api import make_tasks as _make_tasks

_driver = CDEPS
execute = _make_execute(_driver, with_cycle=True)
tasks = _make_tasks(_driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
