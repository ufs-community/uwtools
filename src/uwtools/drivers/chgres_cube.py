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
from uwtools.utils.processing import execute
from uwtools.utils.tasks import file


class ChgresCube(Driver):
    """
    A driver for chgres_cube.
    """

    def __init__(
        self, config_file: Path, cycle: datetime, dry_run: bool = False, batch: bool = False
    ):
        """
        The driver.

        :param config_file: Path to config file.
        :param cycle: The forecast cycle.
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        """
        super().__init__(config_file=config_file, dry_run=dry_run, batch=batch)
        self._config.dereference(context={"cycle": cycle})
        if self._dry_run:
            dryrun()
        self._cycle = cycle
        self._rundir = Path(self._driver_config["run_dir"])

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
        vals = self._driver_config["namelist"]["update_values"]["config"]
        inputs = [
            ("data_dir_input_grid", "atm_files_input_grid"),
            ("data_dir_input_grid", "grib2_file_input_grid"),
            ("data_dir_input_grid", "sfc_files_input_grid"),
            "mosaic_file_target_grid",
            "varmap_file",
            "vcoord_file_target_grid",
        ]
        input_paths = []
        for item in inputs:
            if isinstance(item, str):
                input_paths += [Path(vals[item])]
            else:
                input_paths += [Path(vals[item[0]]) / vals[item[1]]]
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
    def _driver_config(self) -> Dict[str, Any]:
        """
        Returns the config block specific to this driver.
        """
        driver_config: Dict[str, Any] = self._config["chgres_cube"]
        return driver_config

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

    @property
    def _runscript_path(self) -> Path:
        """
        Returns the path to the runscript.
        """
        return self._rundir / "runscript"

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s chgres_cube %s" % (self._cycle.strftime("%Y%m%d %HZ"), suffix)

    def _validate(self) -> None:
        """
        Perform all necessary schema validation.
        """
        for schema_name in ("chgres_cube", "platform"):
            self._validate_one(schema_name=schema_name)
