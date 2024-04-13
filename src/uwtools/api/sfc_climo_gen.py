"""
API access to the ``uwtools`` ``sfc_climo_gen`` driver.
"""

from pathlib import Path
from typing import Dict, Optional, Union

import uwtools.drivers.support as _support
from uwtools.drivers.sfc_climo_gen import SfcClimoGen as _SfcClimoGen
from uwtools.utils.api import ensure_config as _ensure_config


def execute(
    task: str,
    config: Optional[Union[Path, str]] = None,
    batch: bool = False,
    dry_run: bool = False,
    graph_file: Optional[Path] = None,
    stdin_ok: bool = False,
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
    :param stdin_ok: OK to read from stdin?
    :return: ``True`` if task completes without raising an exception.
    """
    obj = _SfcClimoGen(config=_ensure_config(config, stdin_ok), batch=batch, dry_run=dry_run)
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
