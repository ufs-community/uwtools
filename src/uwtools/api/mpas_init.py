"""
API access to the ``uwtools`` ``mpas-init`` driver.
"""

import datetime as dt
from pathlib import Path
from typing import Dict, Optional, Union

import uwtools.drivers.support as _support
from uwtools.drivers.mpas_init import MPASInit as _MPASInit
from uwtools.utils.api import ensure_data_source as _ensure_data_source


def execute(
    task: str,
    cycle: dt.datetime,
    config: Optional[Union[Path, str]] = None,
    batch: bool = False,
    dry_run: bool = False,
    graph_file: Optional[Path] = None,
    stdin_ok: bool = False,
) -> bool:
    """
    Execute an MPAS ``init-atmosphere`` task.

    If ``batch`` is specified, a runscript will be written and submitted to the batch system.
    Otherwise, the executable will be run directly on the current system.

    :param task: The task to execute.
    :param config: Path to config file (read stdin if missing or None).
    :param cycle: The cycle.
    :param batch: Submit run to the batch system?
    :param dry_run: Do not run the executable, just report what would have been done.
    :param graph_file: Write Graphviz DOT output here.
    :param stdin_ok: OK to read from stdin?
    :return: ``True`` if task completes without raising an exception.
    """
    obj = _MPASInit(
        cycle=cycle, config=_ensure_data_source(config, stdin_ok), batch=batch, dry_run=dry_run
    )
    getattr(obj, task)()
    if graph_file:
        with open(graph_file, "w", encoding="utf-8") as f:
            print(graph(), file=f)
    return True


def graph() -> str:
    """
    Returns Graphviz DOT code for the most recently executed task.
    """
    return _support.graph()


def tasks() -> Dict[str, str]:
    """
    Returns a mapping from task names to their one-line descriptions.
    """
    return _support.tasks(_MPASInit)
