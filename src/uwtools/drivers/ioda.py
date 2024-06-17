"""
A driver for the ioda component.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from iotaa import tasks

from uwtools.drivers.jedi import JEDI
from uwtools.strings import STR


class IODA(JEDI):
    """
    A driver for the IODA component.
    """

    def __init__(
        self,
        cycle: datetime,
        config: Optional[Path] = None,
        dry_run: bool = False,
        batch: bool = False,
        key_path: Optional[List[str]] = None,
    ):
        """
        The driver.

        :param cycle: The forecast cycle.
        :param config: Path to config file.
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        :param key_path: Keys leading through the config to the driver's configuration block.
        """
        super().__init__(
            config=config, dry_run=dry_run, batch=batch, cycle=cycle, key_path=key_path
        )
        self._cycle = cycle

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.configuration_file(),
            self.files_copied(),
            self.files_linked(),
            self.runscript(),
        ]

    # Private helper methods

    @property
    def _config_fn(self) -> str:
        """
        Returns the name of the config file used in execution.
        """
        return "ioda.yaml"

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.ioda

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return self._taskname_with_cycle(self._cycle, suffix)
