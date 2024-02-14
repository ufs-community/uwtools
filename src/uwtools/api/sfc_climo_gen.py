from pathlib import Path
from typing import Dict

import iotaa

from uwtools.drivers.sfc_climo_gen import SfcClimoGen


def execute(
    task: str,
    config_file: Path,
    batch: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Execute an sfc_climo_gen task.

    If ``batch`` is specified, a runscript will be written and submitted to the batch system.
    Otherwise, the forecast will be run directly on the current system.

    :param task: The task to execute
    :param config_file: Path to UW YAML config file
    :param batch: Submit run to the batch system
    :param dry_run: Do not run forecast, just report what would have been done
    :return: True if task completes without raising an exception
    """
    obj = SfcClimoGen(config_file=config_file, batch=batch, dry_run=dry_run)
    getattr(obj, task)()
    return True


def tasks() -> Dict[str, str]:
    """
    Returns a mapping from task names to their one-line descriptions.
    """
    return {
        task: getattr(SfcClimoGen, task).__doc__.strip().split("\n")[0]
        for task in iotaa.tasknames(SfcClimoGen)
    }
