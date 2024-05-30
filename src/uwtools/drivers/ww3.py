"""
A library driver for ww3.
"""

from pathlib import Path
from typing import List, Optional

from iotaa import asset, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import Assets
from uwtools.strings import STR


class WaveWatchIII(Assets):
    """
    A library driver for ww3.
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
        fn = "ww3_shel.nml"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield None
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self._driver_config["namelist"],
            path=path,
            schema=self._namelist_schema(),
        )

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [self.namelist_file(), self.restart_directory()]

    @task
    def restart_directory(self):
        """
        The restart directory.
        """
        yield self._taskname("restart directory")
        path = self._rundir / "restart_wave"
        yield asset(path, path.is_dir)
        yield None
        path.mkdir(parents=True)

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.ww3
