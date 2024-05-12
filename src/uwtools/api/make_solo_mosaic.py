"""
API access to the ``uwtools`` ``make_solo_mosaic`` driver.
"""

from uwtools.drivers.make_solo_mosaic import MakeSoloMosaic as _Driver
from uwtools.drivers.support import graph
from uwtools.utils.api import make_execute as _make_execute
from uwtools.utils.api import make_tasks as _make_tasks

execute = _make_execute(_Driver)
tasks = _make_tasks(_Driver)
__all__ = ["execute", "graph", "tasks"]
