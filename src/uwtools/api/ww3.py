"""
API access to the ``uwtools`` ``ww3`` driver.
"""

from uwtools.drivers.support import graph
from uwtools.drivers.ww3 import WaveWatchIII
from uwtools.utils.api import make_execute as _make_execute
from uwtools.utils.api import make_tasks as _make_tasks

_driver = WaveWatchIII
execute = _make_execute(_driver)
tasks = _make_tasks(_driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
