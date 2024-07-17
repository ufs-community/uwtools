"""
API access to the ``uwtools`` ``sfc_climo_gen`` driver.
"""

from functools import partial

from uwtools.drivers.sfc_climo_gen import SfcClimoGen
from uwtools.drivers.support import graph, tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = SfcClimoGen
execute = _make_execute(_driver)
tasks = partial(tasks, _driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
