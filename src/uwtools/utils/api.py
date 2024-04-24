"""
Support for API modules.
"""

import datetime as dt
import re
from functools import partial
from pathlib import Path
from typing import Any, Callable, Optional, Union

from uwtools.config.formats.base import Config
from uwtools.drivers.driver import Driver
from uwtools.drivers.support import graph, tasks
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


def make_execute(
    driver_class: type[Driver], component_name: str, with_cycle: bool
) -> Callable[..., bool]:
    """
    ???
    """

    def del_doc_param(obj: Callable, param: str):
        assert obj.__doc__ is not None
        obj.__doc__ = re.sub(rf"\n *:param {param}:.*\n", "\n", obj.__doc__)

    new = partial(_execute, driver_class)
    new.__doc__ = re.sub(r"<NAME>", component_name, _execute.__doc__ or "")
    del_doc_param(new, "driver_class")
    if not with_cycle:
        del_doc_param(new, "cycle")
    return new


def make_tasks(driver_class: type[Driver]) -> Callable:
    """
    ???
    """
    new = partial(tasks, driver_class)
    new.__doc__ = tasks.__doc__
    return new


def str2path(val: Any) -> Any:
    """
    Return str value as Path, other types unmodified.

    :param val: Any value.
    """
    return Path(val) if isinstance(val, str) else val


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
    Execute a ``<NAME>`` task.

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


def _execute_base(  # pylint: disable=unused-argument
    driver_class: type[Driver],
    task: str,
    config: Optional[Union[Path, str]] = None,
    batch: bool = False,
    dry_run: bool = False,
    graph_file: Optional[Union[Path, str]] = None,
    stdin_ok: bool = False,
) -> bool:
    """
    NB: This docstring is dynamically replaced.
    """
    return _execute(**locals())


_execute_base.__doc__ = re.sub(r"\n:param cycle:.*\n", "\n", _execute.__doc__ or "")


def _execute_cycle(  # pylint: disable=unused-argument
    driver_class: type[Driver],
    task: str,
    cycle: dt.datetime,
    config: Optional[Union[Path, str]] = None,
    batch: bool = False,
    dry_run: bool = False,
    graph_file: Optional[Union[Path, str]] = None,
    stdin_ok: bool = False,
) -> bool:
    """
    NB: This docstring is dynamically replaced.
    """
    return _execute(**locals())


_execute_cycle.__doc__ = _execute.__doc__
