"""
API access to the ``uwtools`` ``make_hgrid`` driver.
"""

from uwtools.drivers.make_hgrid import MakeHgrid
from uwtools.drivers.support import graph
from uwtools.utils.api import make_execute as _make_execute
from uwtools.utils.api import make_tasks as _make_tasks

_driver = MakeHgrid
execute = _make_execute(_driver)
tasks = _make_tasks(_driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
