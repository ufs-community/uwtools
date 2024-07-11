"""
API access to the ``uwtools`` driver base classes.
"""

import importlib
import sys

from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Union
from uwtools.logging import log

def execute(
        module_name: str,
        class_name: str,
        task: str,
        module_path: Optional[str] = None,
        schema_file: Optional[str] = None,
        config: Optional[Union[Path, str]] = None,
        batch: Optional[bool] = False,
        dry_run: Optional[bool] = False,
        key_path: Optional[list[str]] = None,
        stdin_ok: Optional[bool] = False,
        cycle: Optional[datetime] = None,
        leadtime: Optional[timedelta] = None,
):
    
    try:
        module_ = importlib.import_module(module_name)
    except:
        log.error("Provide path to directory that contains module.")
        return False
    try:
        class_ = getattr(module_, class_name)
    except:
        log.error("Could not load driver class %s" % class_name)
        return False
    


    

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
