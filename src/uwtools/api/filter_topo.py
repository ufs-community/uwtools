"""
API access to the ``uwtools`` ``filter_topo`` driver.
"""

from functools import partial

from uwtools.drivers.filter_topo import FilterTopo
from uwtools.drivers.support import graph, tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = FilterTopo
execute = _make_execute(_driver)
tasks = partial(tasks, _driver)
__all__ = ["FilterTopo", "execute", "graph", "tasks"]
