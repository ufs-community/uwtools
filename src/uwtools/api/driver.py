"""
API access to the ``uwtools`` driver base classes.
"""

import importlib
import sys
from datetime import datetime, timedelta
from importlib.util import module_from_spec, spec_from_file_location
from inspect import getfullargspec
from pathlib import Path
from typing import Optional, Type, Union

from uwtools.drivers.support import graph
from uwtools.drivers.support import tasks as _tasks
from uwtools.logging import log
from uwtools.utils.api import ensure_data_source


def execute(  # pylint: disable=unused-argument
    module: str,
    classname: str,
    task: str,
    schema_file: str,
    module_dir: Optional[Union[Path, str]] = None,
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

    :param module: Name of driver module.
    :param classname: Class of driver object to instantiate.
    :param task: The task to execute.
    :param schema_file: Path to schema file.
    :param module_dir: Path to module file.
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
    if not (class_ := _get_driver_class(classname=classname, module=module, module_dir=module_dir)):
        return False
    accepted = set(getfullargspec(class_).args)
    required = accepted & {"cycle", "leadtime"}
    kwargs = dict(
        config=ensure_data_source(config, bool(stdin_ok)),
        dry_run=dry_run,
        key_path=key_path,
        schema_file=schema_file,
    )
    for arg in sorted(["batch", *required]):
        if arg in accepted:
            kwargs[arg] = locals()[arg]
    driverobj = class_(**kwargs)
    log.debug("Instantiated %s with args: %s", classname, kwargs)
    getattr(driverobj, task)()
    if graph_file:
        with open(graph_file, "w", encoding="utf-8") as f:
            print(graph(), file=f)
    return True


def tasks(
    classname: str,
    module: str,
    module_dir: Optional[Union[Path, str]] = None,
) -> dict[str, str]:
    """
    Returns a mapping from task names to their one-line descriptions.

    :param classname: Class of driver object to instantiate.
    :param module_name: Name of driver module.
    :param module_path: Path to module file.
    """
    if not (class_ := _get_driver_class(classname, module, module_dir)):
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
    classname: str, module: str, module_dir: Optional[Union[Path, str]] = None
) -> Optional[Type]:
    """
    Returns the driver class.

    :param classname: Class of driver object to instantiate.
    :param module: Name of driver module.
    :param module_dir: Path to directory that contains module.
    """
    module_dir = Path(module_dir) if module_dir else Path.cwd()
    file_path = (module_dir / module).with_suffix(".py")
    if spec := spec_from_file_location(module, file_path):
        m = module_from_spec(spec)
        if loader := spec.loader:
            try:
                loader.exec_module(m)
            except Exception:  # pylint: disable=broad-exception-caught
                log.error("Could not load module %s", module)
                return None
        if hasattr(m, classname):
            c: Type = getattr(m, classname)
            return c
        log.error("Module %s has no class %s", module, classname)
        return None
    log.error("Could not load module %s", module)
    return None


__all__: list[str] = [graph.__name__]
_add_classes()
