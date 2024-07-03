"""
API access to the ``uwtools`` driver base classes.
"""

import sys
from importlib import import_module


def _add_classes():
    m = import_module("uwtools.drivers.driver")
    for classname in ["Assets"]:
        setattr(sys.modules[__name__], classname, getattr(m, classname))
        __all__.append(classname)


__all__: list[str] = []
_add_classes()
