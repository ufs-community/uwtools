"""
API access to the uwtools FV3 driver.
"""
import datetime as dt
from pathlib import Path
from typing import Dict

import iotaa

from uwtools.drivers.fv3 import FV3


def execute(
    task: str,
    config_file: Path,
    cycle: dt.datetime,
    batch: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Execute an FV3 task.

    If ``batch`` is specified, a runscript will be written and submitted to the batch system.
    Otherwise, the forecast will be run directly on the current system.

    :param task: The task to execute
    :param config_file: Path to UW YAML config file
    :param cycle: The cycle to run
    :param batch: Submit run to the batch system
    :param dry_run: Do not run forecast, just report what would have been done
    :return: True if task completes without raising an exception
    """
    obj = FV3(config_file=config_file, cycle=cycle, batch=batch, dry_run=dry_run)
    getattr(obj, task)()
    return True


def tasks() -> Dict[str, str]:
    """
    Returns a mapping from task names to their one-line descriptions.
    """
    return {
        task: getattr(FV3, task).__doc__.strip().split("\n")[0] for task in iotaa.tasknames(FV3)
    }
