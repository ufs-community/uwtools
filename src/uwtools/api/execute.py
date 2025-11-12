"""
API support for interacting with external drivers.
"""

from __future__ import annotations

from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location
from inspect import getfullargspec
from pathlib import Path
from traceback import format_exc
from typing import TYPE_CHECKING

from uwtools.drivers.support import tasks as _tasks
from uwtools.logging import log
from uwtools.strings import STR
from uwtools.utils.api import ensure_data_source

if TYPE_CHECKING:
    from datetime import datetime, timedelta
    from types import ModuleType

    from iotaa import Node

    from uwtools.config.support import YAMLKey


def execute(
    module: Path | str,
    classname: str,
    task: str,
    schema_file: str | None = None,
    config: Path | str | None = None,
    cycle: datetime | None = None,
    leadtime: timedelta | None = None,
    batch: bool | None = False,
    dry_run: bool | None = False,
    graph_file: Path | str | None = None,
    key_path: list[YAMLKey] | None = None,
    stdin_ok: bool | None = False,
) -> Node | None:
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
    :return: The assets yielded by the task, if it completes without raising an exception.
    """
    class_, module_path = _get_driver_class(module, classname)
    if not class_:
        return None
    assert module_path is not None
    args = dict(locals())
    accepted = set(getfullargspec(class_).args)
    non_optional = {STR.cycle, STR.leadtime}
    for arg in sorted([STR.batch, *non_optional]):
        if args.get(arg) and arg not in accepted:
            log.error("%s does not accept argument '%s'", classname, arg)
            return None
    for arg in sorted(non_optional):
        if arg in accepted and args[arg] is None:
            log.error("%s requires argument '%s'", classname, arg)
            return None
    kwargs = dict(
        config=ensure_data_source(config, bool(stdin_ok)),
        key_path=key_path,
        schema_file=schema_file or module_path.with_suffix(".jsonschema"),
    )
    required = non_optional & accepted
    kwargs.update({arg: args[arg] for arg in sorted([STR.batch, *required]) if arg in accepted})
    driverobj = class_(**kwargs)
    log.debug("Instantiated %s with: %s", classname, kwargs)
    node: Node = getattr(driverobj, task)(dry_run=dry_run)
    if graph_file:
        Path(graph_file).write_text(f"{node.graph}\n")
    return node


def tasks(module: Path | str, classname: str) -> dict[str, str]:
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


def _get_driver_class(module: Path | str, classname: str) -> tuple[type | None, Path | None]:
    """
    Return the driver class.

    :param module: Name of driver module to load.
    :param classname: Name of driver class to instantiate.
    """
    if not (m := _get_driver_module_explicit(Path(module))) and not (
        m := _get_driver_module_implicit(str(module))
    ):
        log.error("Could not load module %s", module)
        return None, None
    assert m.__file__ is not None
    module_path = Path(m.__file__)
    if hasattr(m, classname):
        c: type = getattr(m, classname)
        return c, module_path
    log.error("Module %s has no class %s", module, classname)
    return None, module_path


def _get_driver_module_explicit(module: Path) -> ModuleType | None:
    """
    Return the named module found via explicit lookup of given path.

    :param module: Name of driver module to load.
    """
    log.debug("Loading module %s", module)
    if (spec := spec_from_file_location(module.name, module)) and spec.loader:
        m = module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:  # noqa: BLE001
            for line in format_exc().strip().split("\n"):
                log.error(line)
        else:
            log.debug("Loaded module %s", module)
            return m
    return None


def _get_driver_module_implicit(module: str) -> ModuleType | None:
    """
    Return the named module found via implicit (sys.path-based) lookup.

    :param module: Name of driver module to load.
    """
    log.debug("Loading module %s from sys.path", module)
    try:
        return import_module(module)
    except Exception:  # noqa: BLE001
        return None


__all__ = ["execute", "tasks"]
