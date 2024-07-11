"""
API access to the ``uwtools`` ``ungrib`` driver.
"""

from uwtools.drivers.support import graph
from uwtools.drivers.ungrib import Ungrib
from uwtools.utils.api import make_execute as _make_execute
from uwtools.utils.api import make_tasks as _make_tasks

_driver = Ungrib
execute = _make_execute(_driver, with_cycle=True)
tasks = _make_tasks(_driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
