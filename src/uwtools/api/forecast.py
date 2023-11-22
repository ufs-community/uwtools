from datetime import datetime

from uwtools.drivers.forecast import CLASSES as _CLASSES
from uwtools.types import DefinitePath, OptionalPath


def run(
    model: str,
    cycle: datetime,
    config_file: DefinitePath,
    batch_script: OptionalPath = None,
    dry_run: bool = False,
) -> bool:
    """
    ???
    """
    forecast_class = _CLASSES[model]
    return forecast_class(
        batch_script=batch_script,
        config_file=config_file,
        dry_run=dry_run,
    ).run(cycle=cycle)
