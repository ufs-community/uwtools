from typing import Dict

import iotaa as _iotaa

from uwtools.drivers.driver import Driver


def graph() -> str:
    """
    Returns Graphviz DOT code for the most recently executed task.
    """
    return _iotaa.graph()


def tasks(driver_class: type[Driver]) -> Dict[str, str]:
    """
    Returns a mapping from task names to their one-line descriptions.
    """
    return {
        task: getattr(driver_class, task).__doc__.strip().split("\n")[0]
        for task in _iotaa.tasknames(driver_class)
    }
