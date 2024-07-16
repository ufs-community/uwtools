"""
API access to the ``uwtools`` driver base classes.
"""

import importlib
import sys
from datetime import datetime, timedelta
from inspect import getfullargspec
from pathlib import Path
from typing import Optional, Type, Union

import iotaa as _iotaa

from uwtools.drivers.support import graph
from uwtools.drivers.support import tasks as _tasks
from uwtools.exceptions import UWError
from uwtools.logging import log
from uwtools.utils.api import ensure_data_source


def _get_driver_class(class_name, module_name, module_path) -> Optional[Type]:
    if module_path:
        try:
            module_spec = importlib.util.spec_from_file_location(
                module_name, f"{module_path}/{module_name}.py"
            )
            module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(module)
        except UWError:
            log.error()
            return None
    try:
        module = importlib.import_module(module_name)
    except UWError:
        log.error()
        return None
    try:
        class_ = getattr(module, class_name)
        return class_
    except UWError:
        log.error()
        return None


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
) -> bool:
    if not (class_ := _get_driver_class(class_name, module_name, module_path)):
        log.error("msg")
        return False

    kwargs = dict(
        config=ensure_data_source(config, stdin_ok),
        dry_run=dry_run,
        key_path=key_path,
    )
    argnames = getfullargspec(class_).args

    for arg in ["batch", "cycle", "leadtime"]:
        if arg in argnames:
            kwargs[arg] = locals()[arg]

    for arg in ["cycle", "leadtime"]:
        if not locals()[arg] and arg in argnames:
            log.error("msg")
            return False
    driverobj = class_(**kwargs)
    getattr(driverobj, task)()
    return True


def tasks(class_name, module_name, module_path) -> dict[str, str]:
    if not (class_ := _get_driver_class(class_name, module_name, module_path)):
        log.error()
        return False
    return _tasks(class_)


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
