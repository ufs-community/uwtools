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


def execute(  # pylint: disable=unused-argument
    driver_class: str,
    module_name: str,
    task: str,
    cycle: Optional[datetime] = None,
    leadtime: Optional[timedelta] = None,
    config: Optional[Union[Path, str]] = None,
    module_path: Optional[str] = None,
    schema_file: Optional[str] = None,
    batch: Optional[bool] = False,
    dry_run: Optional[bool] = False,
    key_path: Optional[list[str]] = None,
    stdin_ok: Optional[bool] = False,
) -> bool:
    """
    Execute a task.

    If ``batch`` is specified, a runscript will be written and submitted to the batch system.
    Otherwise, the executable will be run directly on the current system.

    :param driver_class: Class of driver object to instantiate.
    :param module_name: Name of driver module.
    :param task: The task to execute.
    :param cycle: The cycle.
    :param leadtime: The leadtime.
    :param config: Path to config file (read stdin if missing or None).
    :param module_path: Path to module file.
    :param schema_file: Path to schema file.
    :param batch: Submit run to the batch system?
    :param dry_run: Do not run the executable, just report what would have been done.
    :param key_path: Path of keys to subsection of config file.
    :param stdin_ok: OK to read from stdin?
    :return: ``True`` if task completes without raising an exception.
    """
    if not (class_ := _get_driver_class(driver_class, module_name, module_path)):
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


def tasks(driver_class, module_name, module_path) -> dict[str, str]:
    """
    Returns a mapping from task names to their one-line descriptions.

    :param driver_class: Class of driver object to instantiate.
    """
    if not (class_ := _get_driver_class(driver_class, module_name, module_path)):
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


def _get_driver_class(driver_class, module_name, module_path) -> Optional[Type]:
    """
    Returns named atribute of the driver class.

    :param driver_class: Class of driver object to instantiate.
    :param module_name: Name of driver module.
    :param module_path: Path to module file.
    """
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
        class_ = getattr(module, driver_class)
        return class_
    except UWError:
        log.error()
        return None


__all__: list[str] = []
_add_classes()
