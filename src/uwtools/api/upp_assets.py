"""
API access to the ``uwtools`` ``upp_assets`` driver.
"""

from uwtools.drivers.support import tasks as _tasks
from uwtools.drivers.upp_assets import UPPAssets
from uwtools.utils.api import make_execute as _make_execute

_driver = UPPAssets
execute = _make_execute(_driver, with_cycle=True, with_leadtime=True)


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


__all__ = ["UPPAssets", "execute", "schema", "tasks"]
