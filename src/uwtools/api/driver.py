"""
API access to the ``uwtools`` driver base classes.
"""

import sys
from datetime import datetime, timedelta
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from inspect import getfullargspec
from pathlib import Path
from typing import Optional, Type, Union

from uwtools.drivers.support import graph
from uwtools.drivers.support import tasks as _tasks
from uwtools.logging import log
from uwtools.utils.api import ensure_data_source


def execute(  # pylint: disable=unused-argument
    module: Union[Path, str],
    classname: str,
    task: str,
    schema_file: str,
    config: Optional[Union[Path, str]] = None,
    cycle: Optional[datetime] = None,
    leadtime: Optional[timedelta] = None,
    batch: Optional[bool] = False,
    dry_run: Optional[bool] = False,
    graph_file: Optional[Union[Path, str]] = None,
    key_path: Optional[list[str]] = None,
    stdin_ok: Optional[bool] = False,
) -> bool:
    """
    Execute a task.

    If ``batch`` is specified, a runscript will be written and submitted to the batch system.
    Otherwise, the executable will be run directly on the current system.

    :param module: Name of driver module to load.
    :param classname: Name of driver class to instantiate.
    :param task: Name of driver task to execute.
    :param schema_file: Path to schema file.
    :param config: Path to config file (read stdin if missing or None).
    :param cycle: The cycle.
    :param leadtime: The leadtime.
    :param batch: Submit run to the batch system?
    :param dry_run: Do not run the executable, just report what would have been done.
    :param graph_file: Write Graphviz DOT output here.
    :param key_path: Path of keys to subsection of config file.
    :param stdin_ok: OK to read from stdin?
    :return: ``True`` if task completes without raising an exception.
    """
    if not (class_ := _get_driver_class(module, classname)):
        return False
    accepted = set(getfullargspec(class_).args)
    non_optional = {"cycle", "leadtime"}
    required = accepted & non_optional
    kwargs = dict(
        config=ensure_data_source(config, bool(stdin_ok)),
        dry_run=dry_run,
        key_path=key_path,
        schema_file=schema_file,
    )
    for arg in sorted(non_optional):
        if arg in accepted and locals()[arg] is None:
            log.error("%s requires argument '%s'", classname, arg)
            return False
    for arg in sorted(["batch", *required]):
        if arg in accepted:
            kwargs[arg] = locals()[arg]
    driverobj = class_(**kwargs)
    log.debug("Instantiated %s with: %s", classname, kwargs)
    getattr(driverobj, task)()
    if graph_file:
        with open(graph_file, "w", encoding="utf-8") as f:
            print(graph(), file=f)
    return True


def tasks(classname: str, module: str) -> dict[str, str]:
    """
    Returns a mapping from task names to their one-line descriptions.

    :param classname: Class of driver object to instantiate.
    :param module: Name of driver module.
    :param module_path: Path to module file.
    """
    if not (class_ := _get_driver_class(module, classname)):
        log.error("Could not get tasks from class %s in module %s", classname, module)
        return {}
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
    m = import_module("uwtools.drivers.driver")
    for classname in _CLASSNAMES:
        setattr(sys.modules[__name__], classname, getattr(m, classname))
        __all__.append(classname)


def _get_driver_class(module: Union[Path, str], classname: str) -> Optional[Type]:
    """
    Returns the driver class.

    :param module: Name of driver module to load.
    :param classname: Name of driver class to instantiate
    """
    module = str(module)
    m = None
    for file_path in [module, str(Path.cwd() / module)]:
        log.debug("Loading module %s from %s", module, file_path)
        if spec := spec_from_file_location(module, file_path):
            m = module_from_spec(spec)
            if loader := spec.loader:
                try:
                    loader.exec_module(m)
                    break
                except Exception:  # pylint: disable=broad-exception-caught
                    m = None
            else:
                m = None
    if not m:
        try:
            log.debug("Loading module %s from sys.path", module)
            m = import_module(module)
        except Exception:  # pylint: disable=broad-exception-caught
            pass
    if not m:
        log.error("Could not load module %s", module)
        return None
    if hasattr(m, classname):
        c: Type = getattr(m, classname)
        return c
    log.error("Module %s has no class %s", module, classname)
    return None


__all__: list[str] = [graph.__name__]
_add_classes()
