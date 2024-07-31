"""
Driver support.
"""

from typing import Type

import iotaa as _iotaa

from uwtools.drivers.driver import DriverT


def graph() -> str:
    """
    Returns Graphviz DOT code for the most recently executed task.
    """
    return _iotaa.graph()


def set_driver_docstring(driver_class: Type) -> None:
    """
    Appends inherited parameter descriptions to the driver's own docstring.
    """
    header = driver_class.__doc__
    body = driver_class.__mro__[1].__doc__
    assert header is not None
    assert body is not None
    setattr(driver_class, "__doc__", "\n".join([header.strip(), *body.split("\n")[1:]]))


def tasks(driver_class: DriverT) -> dict[str, str]:
    """
    Returns a mapping from task names to their one-line descriptions.

    :param driver_class: Class of driver object to instantiate.
    """
    return {
        task: (getattr(driver_class, task).__doc__ or "").strip().split("\n")[0]
        for task in _iotaa.tasknames(driver_class)
    }
