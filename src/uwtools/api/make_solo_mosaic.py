"""
API access to the ``uwtools`` ``make_solo_mosaic`` driver.
"""

from uwtools.drivers.make_solo_mosaic import MakeSoloMosaic
from uwtools.drivers.support import graph
from uwtools.utils.api import make_execute as _make_execute
from uwtools.utils.api import make_tasks as _make_tasks

_driver = MakeSoloMosaic
execute = _make_execute(_driver)
tasks = _make_tasks(_driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
