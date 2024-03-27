"""
API access to the ``uwtools`` ``sfc_climo_gen`` driver.
"""
from pathlib import Path
from typing import Dict, Optional

import uwtools.drivers.support as _support
from uwtools.drivers.sfc_climo_gen import SfcClimoGen as _SfcClimoGen


def execute(
    task: str,
    config: Optional[Path] = None,
    batch: bool = False,
    dry_run: bool = False,
    graph_file: Optional[Path] = None,
) -> bool:
    """
    Execute an ``sfc_climo_gen`` task.

    If ``batch`` is specified, a runscript will be written and submitted to the batch system.
    Otherwise, the forecast will be run directly on the current system.

    :param task: The task to execute.
    :param config: Path to config file (read stdin if missing or None).
    :param batch: Submit run to the batch system?
    :param dry_run: Do not run forecast, just report what would have been done.
    :param graph_file: Write Graphviz DOT output here.
    :return: ``True`` if task completes without raising an exception.
    """
    obj = _SfcClimoGen(config=config, batch=batch, dry_run=dry_run)
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
    return _support.tasks(_SfcClimoGen)
