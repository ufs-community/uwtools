"""
API access to the ``uwtools`` ``global_equiv_resol`` driver.
"""

from functools import partial

from uwtools.drivers.global_equiv_resol import GlobalEquivResol
from uwtools.drivers.support import graph, tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = GlobalEquivResol
execute = _make_execute(_driver)
tasks = partial(tasks, _driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
