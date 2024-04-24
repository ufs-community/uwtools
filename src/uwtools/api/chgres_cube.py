"""
API access to the uwtools ``chgres_cube`` driver.
"""

import datetime as dt
from functools import partial
from pathlib import Path
from typing import Optional, Union

from uwtools.drivers.chgres_cube import ChgresCube as _Driver
from uwtools.drivers.support import execute as _execute
from uwtools.drivers.support import graph
from uwtools.drivers.support import tasks as _tasks
from uwtools.utils.api import ensure_data_source as _ensure_data_source

__all__ = ["execute", "graph", "tasks"]
tasks = partial(_tasks, _Driver)
tasks.__doc__ = _tasks.__doc__


def execute(
    task: str,
    cycle: dt.datetime,
    config: Optional[Union[Path, str]] = None,
    batch: bool = False,
    dry_run: bool = False,
    graph_file: Optional[Union[Path, str]] = None,
    stdin_ok: bool = False,
) -> bool:
    """
    Execute a ``chgres_cube`` task.

    If ``batch`` is specified, a runscript will be written and submitted to the batch system.
    Otherwise, the executable will be run directly on the current system.

    :param task: The task to execute.
    :param cycle: The cycle.
    :param config: Path to config file (read stdin if missing or None).
    :param batch: Submit run to the batch system?
    :param dry_run: Do not run the executable, just report what would have been done.
    :param graph_file: Write Graphviz DOT output here.
    :param stdin_ok: OK to read from stdin?
    :return: ``True`` if task completes without raising an exception.
    """
    return _execute(
        driver_class=_Driver,
        task=task,
        cycle=cycle,
        config=_ensure_data_source(config, stdin_ok),
        batch=batch,
        dry_run=dry_run,
        graph_file=graph_file,
    )
