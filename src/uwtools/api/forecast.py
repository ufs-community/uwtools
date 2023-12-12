import datetime as dt

from uwtools.drivers.forecast import CLASSES as _CLASSES
from uwtools.types import DefinitePath, OptionalPath


def run(  # pylint: disable=missing-function-docstring
    model: str,
    cycle: dt.datetime,
    config_file: DefinitePath,
    batch_script: OptionalPath = None,
    dry_run: bool = False,
) -> bool:
    forecast_class = _CLASSES[model]
    return forecast_class(
        batch_script=batch_script,
        config_file=config_file,
        dry_run=dry_run,
    ).run(cycle=cycle)


# The following statement dynamically interpolates values into run()'s docstring, which will not
# work if the docstring is inlined in the function. It must remain a separate statement to avoid
# hardcoding values into it.

run.__doc__ = """
Run a forecast model.

If ``batch_script`` is specified, a batch script will be written that, when submitted to the appropriate
scheduler, will run the forecast on batch resources. When not specified, the forecast will be run
immediately on the current system, without creation of a batch script.

:param model: One of: {models}
:param cycle: The cycle to run.
:param config_file: Path to config file for the forecast run.
:param batch_script: Path to a batch script to write.
:param dry_run: Do not run forecast, just report what would have been done.
:return: Success status of requested operation (immediate run or batch-script creation).
""".format(
    models=", ".join(list(_CLASSES.keys()))
).strip()
