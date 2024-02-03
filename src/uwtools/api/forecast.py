import datetime as dt
from typing import List

import iotaa

from uwtools.drivers.forecast import CLASSES
from uwtools.types import DefinitePath

DEFAULT_TASK = "run"


def run(  # pylint: disable=missing-function-docstring
    model: str,
    cycle: dt.datetime,
    config_file: DefinitePath,
    batch: bool = False,
    task: str = DEFAULT_TASK,
    dry_run: bool = False,
) -> bool:
    obj = CLASSES[model](
        batch=batch,
        config_file=config_file,
        cycle=cycle,
        dry_run=dry_run,
    )
    getattr(obj, task)()
    return True


def tasks(model: str) -> List[str]:  # pylint: disable=missing-function-docstring
    return iotaa.tasknames(CLASSES[model])


# The following statement dynamically interpolates values into run()'s docstring, which will not
# work if the docstring is inlined in the function. It must remain a separate statement to avoid
# hardcoding values into it.

run.__doc__ = """
Run a forecast model.

If ``batch`` is specified, a runscript will be written and submitted to the batch system. Otherwise,
the forecast will be run directly on the current system without a runscript.

:param model: One of: {models}
:param cycle: The cycle to run
:param config_file: Path to config file for the forecast run
:param batch: Submit run to the batch system
:param dry_run: Do not run forecast, just report what would have been done
:return: Success status of requested operation
""".format(
    models=", ".join(list(CLASSES.keys()))
).strip()


# The following statement dynamically interpolates values into tasks()'s docstring, which will not
# work if the docstring is inlined in the function. It must remain a separate statement to avoid
# hardcoding values into it.

tasks.__doc__ = """
Returns the names of iotaa tasks in the given object.

:param model: One of: {models}
""".format(
    models=", ".join(list(CLASSES.keys()))
).strip()
