"""
Support for API modules.
"""

import datetime as dt
import re
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from uwtools.config.formats.base import Config
from uwtools.drivers.driver import Driver
from uwtools.drivers.support import graph
from uwtools.drivers.support import tasks as _tasks
from uwtools.exceptions import UWError


def ensure_data_source(
    data_source: Optional[Union[dict, Config, Path, str]], stdin_ok: bool
) -> Any:
    """
    If stdin read is disabled, ensure that a data source was provided. Convert str -> Path.

    :param data_source: Data source as provided to API.
    :param stdin_ok: OK to read from stdin?
    :return: Data source, with a str converted to Path.
    :raises: UWError if no data source was provided and stdin read is disabled.
    """
    if data_source is None and not stdin_ok:
        raise UWError("Set stdin_ok=True to permit read from stdin")
    return str2path(data_source)


def make_execute(driver_class: type[Driver], with_cycle: bool) -> Callable[..., bool]:
    """
    Returns a function that executes tasks for the given driver.

    :param driver_class: The driver class whose tasks to execute.
    :param with_cycle: Does the driver's constructur take the 'cycle' parameter?
    """

    def execute(  # pylint: disable=unused-argument
        task: str,
        config: Optional[Union[Path, str]] = None,
        batch: bool = False,
        dry_run: bool = False,
        graph_file: Optional[Union[Path, str]] = None,
        stdin_ok: bool = False,
    ) -> bool:
        return _execute(driver_class, **locals())

    def execute_cycle(  # pylint: disable=unused-argument
        task: str,
        cycle: dt.datetime,
        config: Optional[Union[Path, str]] = None,
        batch: bool = False,
        dry_run: bool = False,
        graph_file: Optional[Union[Path, str]] = None,
        stdin_ok: bool = False,
    ) -> bool:
        return _execute(driver_class, **locals())

    assert _execute.__doc__ is not None
    execute_cycle.__doc__ = re.sub(r"\n *:param driver_class:.*\n", "\n", _execute.__doc__)
    execute.__doc__ = re.sub(r"\n *:param cycle:.*\n", "\n", execute_cycle.__doc__)

    if with_cycle:
        return execute_cycle
    return execute


def make_tasks(driver_class: type[Driver]) -> Callable[..., Dict[str, str]]:
    """
    Returns a function that maps task names to descriptions for the given driver.

    :param driver_class: The driver class whose tasks and descriptions to map.
    """

    def tasks() -> Dict[str, str]:
        """
        Returns a mapping from task names to their one-line descriptions.
        """
        return _tasks(driver_class)

    return tasks


def str2path(val: Any) -> Any:
    """
    Return str value as Path, other types unmodified.

    :param val: Any value.
    """
    return Path(val) if isinstance(val, str) else val


# Private


def _execute(
    driver_class: type[Driver],
    task: str,
    cycle: Optional[dt.datetime] = None,
    config: Optional[Union[Path, str]] = None,
    batch: bool = False,
    dry_run: bool = False,
    graph_file: Optional[Union[Path, str]] = None,
    stdin_ok: bool = False,
) -> bool:
    """
    Execute a task.

    If ``batch`` is specified, a runscript will be written and submitted to the batch system.
    Otherwise, the executable will be run directly on the current system.

    :param driver_class: Class of driver object to instantiate.
    :param task: The task to execute.
    :param cycle: The cycle.
    :param config: Path to config file (read stdin if missing or None).
    :param batch: Submit run to the batch system?
    :param dry_run: Do not run the executable, just report what would have been done.
    :param graph_file: Write Graphviz DOT output here.
    :param stdin_ok: OK to read from stdin?
    :return: ``True`` if task completes without raising an exception.
    """
    kwargs = dict(
        config=ensure_data_source(config, stdin_ok),
        batch=batch,
        dry_run=dry_run,
    )
    if cycle:
        kwargs["cycle"] = cycle
    obj = driver_class(**kwargs)
    getattr(obj, task)()
    if graph_file:
        with open(graph_file, "w", encoding="utf-8") as f:
            print(graph(), file=f)
    return True
