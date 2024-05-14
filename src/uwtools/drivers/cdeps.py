"""
A driver for the CDEPS data models.
"""

from datetime import datetime
from pathlib import Path
from shutil import copy
from typing import Optional

from iotaa import asset, dryrun, task, tasks

from uwtools.api.template import render
from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import Driver
from uwtools.logging import log
from uwtools.strings import STR
from uwtools.utils.tasks import file, filecopy, symlink


class CDEPS(Driver):
    """
    A driver for the CDEPS data models.
    """

    def __init__(
        self,
        cycle: datetime,
        config: Optional[Path] = None,
        dry_run: bool = False,
        batch: bool = False,
    ):
        """
        The driver.

        :param cycle: The cycle.
        :param config: Path to config file (read stdin if missing or None).
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        """
        super().__init__(config=config, dry_run=dry_run, batch=batch, cycle=cycle)
        if self._dry_run:
            dryrun()
        self._cycle = cycle

    # Workflow tasks

    @task
    def atm(self):
        """
        The atm namelist file.
        """
        fn = "datm_in"
        yield self._taskname(f"namelist file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._model_namelist_file("atm_in", path)

    @task
    def ocn(self):
        """
        The ocn namelist file.
        """
        fn = "docn_in"
        yield self._taskname(f"namelist file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._model_namelist_file("ocn_in", path)

    def _model_namelist_file(self, group: str, path: str):
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self._driver_config[group],
            path=path,
        )

    @task
    def atm_stream(self):
        fn = "datm.streams"
        yield self._taskname(f"namelist file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield file(path=Path(self._driver_config["atm_streams"]["base_file"]))
        render(
            input_file=Path(self._driver_config["atm_streams"]["base_file"]),
            output_file=path,
            values_src=self._driver_config["atm_streams"],
        )

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.cdeps

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s %s" % (self._cycle.strftime("%Y%m%d %HZ"), self._driver_name, suffix)
