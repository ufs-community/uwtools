"""
API access to the ``uwtools`` ``jedi`` driver.
"""

from uwtools.drivers.jedi import JEDI
from uwtools.drivers.support import graph
from uwtools.utils.api import make_execute as _make_execute
from uwtools.utils.api import make_tasks as _make_tasks

_driver = JEDI
execute = _make_execute(_driver, with_cycle=True)
tasks = _make_tasks(_driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
