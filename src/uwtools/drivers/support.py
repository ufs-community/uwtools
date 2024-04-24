from typing import Dict

import iotaa as _iotaa

from uwtools.drivers.driver import Driver


def execute(driver_class: type[Driver], **kwargs) -> bool:
    """
    Execute a driver task.

    :param driver_class: Class of driver object to instantiate.
    :param task: The task to execute.
    :return: ``True`` if task completes without raising an exception.
    """
    obj = driver_class(**kwargs)
    getattr(obj, kwargs["task"])()
    if graph_file := kwargs["graph_file"]:
        with open(graph_file, "w", encoding="utf-8") as f:
            print(graph(), file=f)
    return True


def graph() -> str:
    """
    Returns Graphviz DOT code for the most recently executed task.
    """
    return _iotaa.graph()


def tasks(driver_class: type[Driver]) -> Dict[str, str]:
    """
    Returns a mapping from task names to their one-line descriptions.

    :param driver_class: Class of driver object to instantiate.
    """
    return {
        task: getattr(driver_class, task).__doc__.strip().split("\n")[0]
        for task in _iotaa.tasknames(driver_class)
    }
