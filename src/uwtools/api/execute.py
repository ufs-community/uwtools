"""
API support for interacting with external drivers.
"""

from datetime import datetime, timedelta
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from inspect import getfullargspec
from pathlib import Path
from types import ModuleType
from typing import Optional, Type, Union

from uwtools.drivers.support import graph
from uwtools.drivers.support import tasks as _tasks
from uwtools.logging import log
from uwtools.strings import STR
from uwtools.utils.api import ensure_data_source


def execute(
    module: Union[Path, str],
    classname: str,
    task: str,
    schema_file: Optional[str] = None,
    config: Optional[Union[Path, str]] = None,
    cycle: Optional[datetime] = None,  # pylint: disable=unused-argument
    leadtime: Optional[timedelta] = None,  # pylint: disable=unused-argument
    batch: Optional[bool] = False,  # pylint: disable=unused-argument
    dry_run: Optional[bool] = False,
    graph_file: Optional[Union[Path, str]] = None,
    key_path: Optional[list[str]] = None,
    stdin_ok: Optional[bool] = False,
) -> bool:
    """
    Execute a driver task.

    If ``batch`` is specified and the driver is instructed to run, its runscript will be configured
    for and submitted to the batch system. Otherwise, the executable will be run directly on the
    current system.

    :param module: Path to driver module or name of module on sys.path.
    :param classname: Name of driver class to instantiate.
    :param task: Name of driver task to execute.
    :param schema_file: The JSON Schema file to use for validation.
    :param config: Path to config file (read stdin if missing or None).
    :param cycle: The cycle.
    :param leadtime: The leadtime.
    :param batch: Submit run to the batch system?
    :param dry_run: Do not run the executable, just report what would have been done.
    :param graph_file: Write Graphviz DOT output here.
    :param key_path: Path of keys to config block to use.
    :param stdin_ok: OK to read from stdin?
    :return: ``True`` if task completes without raising an exception.
    """
    class_, module_path = _get_driver_class(module, classname)
    if not class_:
        return False
    assert module_path is not None
    args = dict(locals())
    accepted = set(getfullargspec(class_).args)
    non_optional = {STR.cycle, STR.leadtime}
    for arg in sorted([STR.batch, *non_optional]):
        if args.get(arg) and arg not in accepted:
            log.error("%s does not accept argument '%s'", classname, arg)
            return False
    for arg in sorted(non_optional):
        if arg in accepted and args[arg] is None:
            log.error("%s requires argument '%s'", classname, arg)
            return False
    kwargs = dict(
        config=ensure_data_source(config, bool(stdin_ok)),
        dry_run=dry_run,
        key_path=key_path,
        schema_file=schema_file or module_path.with_suffix(".jsonschema"),
    )
    required = non_optional & accepted
    for arg in sorted([STR.batch, *required]):
        if arg in accepted:
            kwargs[arg] = args[arg]
    driverobj = class_(**kwargs)
    log.debug("Instantiated %s with: %s", classname, kwargs)
    getattr(driverobj, task)()
    if graph_file:
        with open(graph_file, "w", encoding="utf-8") as f:
            print(graph(), file=f)
    return True


def tasks(module: Union[Path, str], classname: str) -> dict[str, str]:
    """
    Return a mapping from driver task names to their one-line descriptions.

    :param module: Name of driver module.
    :param classname: Name of driver class to instantiate.
    """
    class_, _ = _get_driver_class(module, classname)
    if not class_:
        log.error("Could not get tasks from class %s in module %s", classname, module)
        return {}
    return _tasks(class_)


def _get_driver_class(
    module: Union[Path, str], classname: str
) -> tuple[Optional[Type], Optional[Path]]:
    """
    Return the driver class.

    :param module: Name of driver module to load.
    :param classname: Name of driver class to instantiate.
    """
    if not (m := _get_driver_module_explicit(Path(module))):
        if not (m := _get_driver_module_implicit(str(module))):
            log.error("Could not load module %s", module)
            return None, None
    assert m.__file__ is not None
    module_path = Path(m.__file__)
    if hasattr(m, classname):
        c: Type = getattr(m, classname)
        return c, module_path
    log.error("Module %s has no class %s", module, classname)
    return None, module_path


def _get_driver_module_explicit(module: Path) -> Optional[ModuleType]:
    """
    Return the named module found via explicit lookup of given path.

    :param module: Name of driver module to load.
    """
    log.debug("Loading module %s", module)
    if spec := spec_from_file_location(module.name, module):
        m = module_from_spec(spec)
        if loader := spec.loader:
            try:
                loader.exec_module(m)
                log.debug("Loaded module %s", module)
                return m
            except Exception:  # pylint: disable=broad-exception-caught
                pass
    return None


def _get_driver_module_implicit(module: str) -> Optional[ModuleType]:
    """
    Return the named module found via implicit (sys.path-based) lookup.

    :param module: Name of driver module to load.
    """
    log.debug("Loading module %s from sys.path", module)
    try:
        return import_module(module)
    except Exception:  # pylint: disable=broad-exception-caught
        return None


__all__ = ["execute", "graph", "tasks"]
