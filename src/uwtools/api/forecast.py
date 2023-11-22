from datetime import datetime

import uwtools.drivers.forecast
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
    forecast_class = uwtools.drivers.forecast.CLASSES[model]
    return forecast_class(
        batch_script=batch_script,
        config_file=config_file,
        dry_run=dry_run,
    ).run(cycle=cycle)
