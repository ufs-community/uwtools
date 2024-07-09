"""
API access to the ``uwtools`` driver base classes.
"""

import importlib
import sys

_CLASSNAMES = [
    "Assets",
    "AssetsCycleBased",
    "AssetsCycleAndLeadtimeBased",
    "AssetsTimeInvariant",
    "Driver",
    "DriverCycleBased",
    "DriverCycleAndLeadtimeBased",
    "DriverTimeInvariant",
]


def _add_classes():
    m = importlib.import_module("uwtools.drivers.driver")
    for classname in _CLASSNAMES:
        setattr(sys.modules[__name__], classname, getattr(m, classname))
        __all__.append(classname)


__all__: list[str] = []
_add_classes()
