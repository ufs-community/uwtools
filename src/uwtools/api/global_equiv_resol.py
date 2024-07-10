"""
API access to the ``uwtools`` ``global_equiv_resol`` driver.
"""

from uwtools.drivers.global_equiv_resol import GlobalEquivResol
from uwtools.drivers.support import graph
from uwtools.utils.api import make_execute as _make_execute
from uwtools.utils.api import make_tasks as _make_tasks

_driver = GlobalEquivResol
execute = _make_execute(_driver)
tasks = _make_tasks(_driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
