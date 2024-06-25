"""
A driver for shave.
"""

from pathlib import Path
from typing import Optional

from iotaa import tasks

from uwtools.drivers.driver import Driver
from uwtools.strings import STR


class Shave(Driver):
    """
    A driver for shave.
    """

    def __init__(
        self,
        config: Optional[Path] = None,
        dry_run: bool = False,
        batch: bool = False,
        key_path: Optional[list[str]] = None,
    ):
        """
        The driver.

        :param config: Path to config file (read stdin if missing or None).
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        :param key_path: Keys leading through the config to the driver's configuration block.
        """
        super().__init__(config=config, dry_run=dry_run, batch=batch, key_path=key_path)

    # Workflow tasks

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield self.runscript()

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.shave

    @property
    def _runcmd(self):
        """
        Returns the full command-line component invocation.
        """
        executable = self._driver_config["execution"]["executable"]
        config = self._driver_config["config"]
        input_file = config["input_grid_file"]
        output_file = input_file.replace(".nc", "_NH0.nc")
        flags = [config[key] for key in ["nx", "ny", "nh4", "input_grid_file"]]
        flags.append(output_file)
        return f"{executable} {' '.join(str(flag) for flag in flags)}"
