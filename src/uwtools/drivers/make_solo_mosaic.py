"""
A driver for make_solo_mosaic.
"""

from pathlib import Path
from typing import Optional

from iotaa import tasks

from uwtools.drivers.driver import Driver
from uwtools.strings import STR


class MakeSoloMosaic(Driver):
    """
    A driver for make_solo_mosaic.
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
        super().__init__(config=config, dry_run=dry_run, batch=batch)

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
        return STR.makesolomosaic

    @property
    def _runcmd(self):
        """
        Returns the full command-line component invocation.
        """
        executable = self._driver_config["execution"]["executable"]
        flags = " ".join(f"--{k} {v}" for k, v in self._driver_config["config"].items())
        return f"{executable} {flags}"

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s" % (self._driver_name, suffix)
