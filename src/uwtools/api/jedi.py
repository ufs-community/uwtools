"""
API access to the ``uwtools`` ``jedi`` driver.
"""
from pathlib import Path
from typing import Dict, Optional

import uwtools.drivers.support as _support
from uwtools.drivers.jedi import Jedi as _Jedi

def execute(
    task: str,
    config_file: Path,
    cycle: dt.datetime,
    batch: bool = False,
    dry_run: bool = False,
    graph_file: Optional[Path] = None,
) -> bool:
    """
    Execute a jedi task.
    If ``batch`` is specified, a runscript will be written and submitted to the batch system.
    Otherwise, the executable will be run directly on the current system.
    :param task: The task to execute
    :param config_file: Path to YAML config file
    :param cycle: The cycle to run
    :param batch: Submit run to the batch system
    :param dry_run: Do not run the executable, just report what would have been done
    :param graph_file: Write Graphviz DOT output here
    :return: True if task completes without raising an exception
    """
    obj = _Jedi(config_file=config_file, cycle=cycle, batch=batch, dry_run=dry_run)
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
    return _support.tasks(_Jedi)
