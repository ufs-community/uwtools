"""
API access to the ``uwtools`` driver base classes.
"""

import importlib
import sys
from datetime import datetime, timedelta
from inspect import getfullargspec
from pathlib import Path
from typing import Optional, Type, Union

from uwtools.drivers.support import graph
from uwtools.drivers.support import tasks as _tasks
from uwtools.logging import log
from uwtools.utils.api import ensure_data_source


def execute(  # pylint: disable=unused-argument
    module: str,
    class_name: str,
    task: str,
    schema_file: str,
    cycle: Optional[datetime] = None,
    leadtime: Optional[timedelta] = None,
    config: Optional[Union[Path, str]] = None,
    module_dir: Optional[str] = None,
    batch: Optional[bool] = False,
    dry_run: Optional[bool] = False,
    key_path: Optional[list[str]] = None,
    stdin_ok: Optional[bool] = False,
) -> bool:
    """
    Execute a task.

    If ``batch`` is specified, a runscript will be written and submitted to the batch system.
    Otherwise, the executable will be run directly on the current system.

    :param class_name: Class of driver object to instantiate.
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
    if not (class_ := _get_driver_class(class_name, module, module_dir)):
        return False

    kwargs = dict(
        config=ensure_data_source(config, bool(stdin_ok)),
        dry_run=dry_run,
        key_path=key_path,
    )
    argnames = getfullargspec(class_).args

    for arg in ["batch", "cycle", "leadtime"]:
        if arg in argnames:
            kwargs[arg] = locals()[arg]

    for arg in ["cycle", "leadtime"]:
        if not locals()[arg] and arg in argnames:
            log.error("%s requires argument %s.", class_name, arg)
            return False
        if locals()[arg] and arg not in argnames:
            log.error("%s is not requried in %s.", arg, class_name)
            return False
    driverobj = class_(**kwargs)
    getattr(driverobj, task)()
    return True


def tasks(
    class_name: str,
    module: str,
    module_dir: Optional[str] = None,
) -> dict[str, str]:
    """
    Returns a mapping from task names to their one-line descriptions.

    :param class_name: Class of driver object to instantiate.
    :param module_name: Name of driver module.
    :param module_path: Path to module file.
    """
    if not (class_ := _get_driver_class(class_name, module, module_dir)):
        log.error("Directory %s not found.", module_dir)
        raise NotADirectoryError
    return _tasks(class_)


_CLASSNAMES = [
    "Assets",
    "AssetsCycleBased",
    "AssetsCycleLeadtimeBased",
    "AssetsTimeInvariant",
    "Driver",
    "DriverCycleBased",
    "DriverCycleLeadtimeBased",
    "DriverTimeInvariant",
]


def _add_classes():
    m = importlib.import_module("uwtools.drivers.driver")
    for classname in _CLASSNAMES:
        setattr(sys.modules[__name__], classname, getattr(m, classname))
        __all__.append(classname)


def _get_driver_class(
    class_name: str,
    module: str,
    module_dir: Optional[str] = None,
) -> Optional[Type]:
    """
    Returns the driver class.

    :param class_name: Class of driver object to instantiate.
    :param module: Name of driver module.
    :param module_dir: Path to directory that contains module.
    """
    try:
        user_path = str(module_dir or Path.cwd())
        sys.path.insert(0, user_path)
        if not module_dir:
            log.info("Added %s search path", user_path)
        module_ = importlib.import_module(module)
    except ModuleNotFoundError:
        if module_dir:
            log.error("Module %s not found in %s", module, module_dir)
        else:
            log.error("No module named %s on path, including %s.", module, Path.cwd())
        return None
    try:
        class_: Type = getattr(module_, class_name)
        return class_
    except AttributeError:
        log.error("Module %s has no class %s.", module, class_name)
        return None


__all__: list[str] = [graph.__name__]
_add_classes()
