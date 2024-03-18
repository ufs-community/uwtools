"""
API access to the uwtools FV3 driver.
"""
import datetime as dt
from pathlib import Path
from typing import Dict, Optional

from uwtools.drivers import support
from uwtools.drivers.fv3 import FV3 as _FV3


def execute(
    task: str,
    config_file: Path,
    cycle: dt.datetime,
    batch: bool = False,
    dry_run: bool = False,
    graph_file: Optional[Path] = None,
) -> bool:
    """
    Execute an FV3 task.

    If ``batch`` is specified, a runscript will be written and submitted to the batch system.
    Otherwise, the forecast will be run directly on the current system.

    :param task: The task to execute
    :param config_file: Path to YAML config file
    :param cycle: The cycle to run
    :param batch: Submit run to the batch system
    :param dry_run: Do not run forecast, just report what would have been done
    :param graph_file: Write Graphviz DOT output here
    :return: ``True`` if task completes without raising an exception
    """
    obj = _FV3(config_file=config_file, cycle=cycle, batch=batch, dry_run=dry_run)
    getattr(obj, task)()
    if graph_file:
        with open(graph_file, "w", encoding="utf-8") as f:
            print(graph(), file=f)
    return True


def graph() -> str:
    """
    Returns Graphviz DOT code for the most recently executed task.
    """
    return support.graph()


def tasks() -> Dict[str, str]:
    """
    Returns a mapping from task names to their one-line descriptions.
    """
    return support.tasks(_FV3)
