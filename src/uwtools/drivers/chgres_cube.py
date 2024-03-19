"""
A driver for chgres_cube.
"""

import os
import stat
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from iotaa import asset, dryrun, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import Driver
from uwtools.strings import STR
from uwtools.utils.tasks import file


class ChgresCube(Driver):
    """
    A driver for chgres_cube.
    """

    _driver_name = STR.chgrescube

    def __init__(self, config: Path, cycle: datetime, dry_run: bool = False, batch: bool = False):
        """
        The driver.

        :param config: Path to config file (read stdin if missing or None).
        :param cycle: The date cycle.
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        """
        super().__init__(config=config, dry_run=dry_run, batch=batch)
        self._config.dereference(context={"cycle": cycle})
        if self._dry_run:
            dryrun()
        self._cycle = cycle

    # Workflow tasks

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        fn = "fort.41"
        yield self._taskname(f"namelist file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        config_files = self._driver_config["namelist"]["update_values"]["config"]
        input_paths = [
            Path(config_files[k])
            for k in ("mosaic_file_target_grid", "varmap_file", "vcoord_file_target_grid")
        ] + [
            Path(config_files["data_dir_input_grid"]) / config_files[k]
            for k in ("atm_files_input_grid", "grib2_file_input_grid", "sfc_files_input_grid")
        ]
        yield [file(input_path) for input_path in input_paths]
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self._driver_config.get("namelist", {}),
            path=path,
        )

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.namelist_file(),
            self.runscript(),
        ]

    @task
    def runscript(self):
        """
        The runscript.
        """
        path = self._runscript_path
        yield self._taskname(path.name)
        yield asset(path, path.is_file)
        yield None

        envvars = {
            "KMP_AFFINITY": "scatter",
            "OMP_NUM_THREADS": self._driver_config.get("execution", {}).get("threads", 1),
            "OMP_STACKSIZE": "1024m",
        }
        envcmds = self._driver_config.get("execution", {}).get("envcmds", [])
        execution = [self._runcmd, "test $? -eq 0 && touch %s/done" % self._rundir]
        scheduler = self._scheduler if self._batch else None
        path.parent.mkdir(parents=True, exist_ok=True)
        rs = self._runscript(
            envcmds=envcmds, envvars=envvars, execution=execution, scheduler=scheduler
        )
        with open(path, "w", encoding="utf-8") as f:
            print(rs, file=f)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)

    # Private helper methods

    @property
    def _resources(self) -> Dict[str, Any]:
        """
        Returns configuration data for the runscript.
        """
        return {
            "account": self._config["platform"]["account"],
            "rundir": self._rundir,
            "scheduler": self._config["platform"]["scheduler"],
            **self._driver_config.get("execution", {}).get("batchargs", {}),
        }

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s %s" % (self._cycle.strftime("%Y%m%d %HZ"), self._driver_name, suffix)
