"""
Driver support.
"""

import re

from iotaa import tasknames as _tasknames

from uwtools.drivers.driver import DriverT


def set_driver_docstring(driver_class: type) -> None:
    """
    Append inherited parameter descriptions to the driver's own docstring.

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
    driver_class.__doc__ = new


def tasks(driver_class: DriverT) -> dict[str, str]:
    """
    Return a mapping from task names to their one-line descriptions.

    :param driver_class: Class of driver object to instantiate.
    """
    return {
        task: (getattr(driver_class, task).__doc__ or "").strip().split("\n")[0]
        for task in _tasknames(driver_class)
    }
