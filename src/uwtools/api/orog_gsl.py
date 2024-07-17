"""
API access to the ``uwtools`` ``orog_gsl`` driver.
"""

from functools import partial

from uwtools.drivers.orog_gsl import OrogGSL
from uwtools.drivers.support import graph, tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = OrogGSL
execute = _make_execute(_driver)
tasks = partial(tasks, _driver)
__all__ = [_driver.__name__, "execute", "graph", "tasks"]
