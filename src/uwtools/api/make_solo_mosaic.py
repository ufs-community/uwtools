"""
API access to the ``uwtools`` ``make_solo_mosaic`` driver.
"""

from uwtools.drivers.make_solo_mosaic import MakeSoloMosaic
from uwtools.drivers.support import tasks as _tasks
from uwtools.utils.api import make_execute as _make_execute

_driver = MakeSoloMosaic
execute = _make_execute(_driver)


def schema() -> dict:
    """
    Return the driver's schema.
    """
    return _driver.schema()


def tasks() -> dict[str, str]:
    """
    Return a mapping from task names to their one-line descriptions.
    """
    return _tasks(_driver)


__all__ = ["MakeSoloMosaic", "execute", "schema", "tasks"]
