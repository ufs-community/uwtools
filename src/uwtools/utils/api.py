"""
Support for API modules.
"""

from __future__ import annotations

import re
from inspect import getfullargspec
from pathlib import Path
from typing import TYPE_CHECKING, Callable, TypeVar

from uwtools.exceptions import UWError
from uwtools.utils.file import str2path

if TYPE_CHECKING:
    import datetime as dt

    from uwtools.config.support import YAMLKey
    from uwtools.drivers.driver import DriverT

T = TypeVar("T")

# Public


def ensure_data_source(data_source: T, stdin_ok: bool) -> T:
    """
    If stdin read is disabled, ensure that a data source was provided.

    :param data_source: Data source as provided to API.
    :param stdin_ok: OK to read from stdin?
    :return: Data source.
    :raises: UWError if no data source was provided and stdin read is disabled.
    """
    if data_source is None and not stdin_ok:
        msg = "Set stdin_ok=True to permit read from stdin"
        raise UWError(msg)
    return data_source


def make_execute(
    driver_class: DriverT,
    with_cycle: bool | None = False,
    with_leadtime: bool | None = False,
) -> Callable[..., bool]:
    """
    Return a function that executes tasks for the given driver.

    :param driver_class: The driver class whose tasks to execute.
    :param with_cycle: Does the driver's constructor take a 'cycle' parameter?
    :param with_leadtime: Does the driver's constructor take a 'leadtime' parameter?
    """

    def execute(
        task: str,
        config: Path | str | None = None,
        batch: bool = False,
        dry_run: bool = False,
        graph_file: Path | str | None = None,
        key_path: list[YAMLKey] | None = None,
        schema_file: Path | str | None = None,
        stdin_ok: bool = False,
    ) -> bool:
        return _execute(
            driver_class=driver_class,
            task=task,
            cycle=None,
            leadtime=None,
            config=config,
            batch=batch,
            dry_run=dry_run,
            graph_file=graph_file,
            key_path=key_path,
            schema_file=schema_file,
            stdin_ok=stdin_ok,
        )

    def execute_cycle(
        task: str,
        cycle: dt.datetime,
        config: Path | str | None = None,
        batch: bool = False,
        dry_run: bool = False,
        graph_file: Path | str | None = None,
        key_path: list[YAMLKey] | None = None,
        schema_file: Path | str | None = None,
        stdin_ok: bool = False,
    ) -> bool:
        return _execute(
            driver_class=driver_class,
            task=task,
            leadtime=None,
            cycle=cycle,
            config=config,
            batch=batch,
            dry_run=dry_run,
            graph_file=graph_file,
            key_path=key_path,
            schema_file=schema_file,
            stdin_ok=stdin_ok,
        )

    def execute_cycle_leadtime(
        task: str,
        cycle: dt.datetime,
        leadtime: dt.timedelta,
        config: Path | str | None = None,
        batch: bool = False,
        dry_run: bool = False,
        graph_file: Path | str | None = None,
        key_path: list[YAMLKey] | None = None,
        schema_file: Path | str | None = None,
        stdin_ok: bool = False,
    ) -> bool:
        return _execute(
            driver_class=driver_class,
            task=task,
            cycle=cycle,
            leadtime=leadtime,
            config=config,
            batch=batch,
            dry_run=dry_run,
            graph_file=graph_file,
            key_path=key_path,
            schema_file=schema_file,
            stdin_ok=stdin_ok,
        )

    execute_cycle_leadtime.__name__ = "execute"
    execute_cycle.__name__ = "execute"
    assert _execute.__doc__ is not None
    execute_cycle_leadtime.__doc__ = re.sub(r"\n *:param driver_class:.*\n", "\n", _execute.__doc__)
    execute_cycle.__doc__ = re.sub(
        r"\n *:param leadtime:.*\n", "\n", execute_cycle_leadtime.__doc__
    )
    execute.__doc__ = re.sub(r"\n *:param cycle:.*\n", "\n", execute_cycle.__doc__)

    if with_leadtime and not with_cycle:
        msg = "When leadtime is specified, cycle is required"
        raise UWError(msg)

    if with_cycle:
        if with_leadtime:
            return execute_cycle_leadtime
        return execute_cycle
    return execute


# Private


def _execute(
    driver_class: DriverT,
    task: str,
    config: Path | str | None = None,
    cycle: dt.datetime | None = None,
    leadtime: dt.timedelta | None = None,
    batch: bool = False,
    dry_run: bool = False,
    graph_file: Path | str | None = None,
    key_path: list[YAMLKey] | None = None,
    schema_file: Path | str | None = None,
    stdin_ok: bool = False,
) -> bool:
    """
    Execute a task.

    If ``batch`` is specified, a runscript will be written and submitted to the batch system.
    Otherwise, the executable will be run directly on the current system.

    :param driver_class: Class of driver object to instantiate.
    :param task: The task to execute.
    :param config: Path to config file (read stdin if missing or None).
    :param cycle: The cycle.
    :param leadtime: The leadtime.
    :param batch: Submit run to the batch system?
    :param dry_run: Do not run the executable, just report what would have been done.
    :param graph_file: Write Graphviz DOT output here.
    :param key_path: Path of keys to config block to use.
    :param schema_file: The JSON Schema file to use for validation.
    :param stdin_ok: OK to read from stdin?
    :return: ``True`` if task completes without raising an exception.
    """
    kwargs = dict(
        config=ensure_data_source(str2path(config), stdin_ok),
        key_path=key_path,
        schema_file=schema_file,
    )
    accepted = set(getfullargspec(driver_class).args)
    for arg in ["batch", "cycle", "leadtime"]:
        if arg in accepted:
            kwargs[arg] = locals()[arg]
    obj = driver_class(**kwargs)
    node = getattr(obj, task)(dry_run=dry_run)
    if graph_file:
        Path(graph_file).write_text(f"{node.graph}\n")
    return True
