"""
API access to the ``uwtools`` ``make_solo_mosaic`` driver.
"""

from functools import partial

from uwtools.drivers.make_solo_mosaic import MakeSoloMosaic
from uwtools.drivers.support import graph, tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = MakeSoloMosaic
execute = _make_execute(_driver)
tasks = partial(tasks, _driver)
__all__ = ["MakeSoloMosaic", "execute", "graph", "tasks"]
