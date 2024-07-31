"""
Driver support.
"""

import re
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

    :param driver_class: The class whose docstring to update.
    """
    head_old = driver_class.__doc__
    assert head_old is not None
    head = head_old.strip()
    parent_class = driver_class.__mro__[1]
    body_old = parent_class.__doc__
    assert body_old is not None
    body = re.sub(r"\n\n+", "\n", body_old.strip()).split("\n")[1:]
    new = "\n".join([f"{head}\n", *body])
    setattr(driver_class, "__doc__", new)


def tasks(driver_class: DriverT) -> dict[str, str]:
    """
    Returns a mapping from task names to their one-line descriptions.

    :param driver_class: Class of driver object to instantiate.
    """
    return {
        task: (getattr(driver_class, task).__doc__ or "").strip().split("\n")[0]
        for task in _iotaa.tasknames(driver_class)
    }
