"""
A driver for ww3.
"""

from pathlib import Path
from typing import List, Optional

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import Driver
from uwtools.strings import STR


class WaveWatchIII(Driver):
    """
    A driver for ww3.
    """

    def __init__(
        self,
        config: Optional[Path] = None,
        dry_run: bool = False,
        batch: bool = False,
        key_path: Optional[List[str]] = None,
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

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        path = self._namelist_path
        yield self._taskname(str(path))
        yield asset(path, path.is_file)
        yield None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self._driver_config["namelist"],
            path=path,
        )

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [self.namelist_file(), self.restart_directory()]

    @tasks
    def restart_directory(self):
        """
        Files copied for run.
        """
        yield self._taskname("restart directory")
        fn = "restart_wave"
        path = self._rundir / fn
        yield asset(path, path.is_dir)

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.ww3

    @property
    def _namelist_path(self) -> Path:
        """
        Path to the namelist file.
        """
        return self._rundir / "namelists.nml"
