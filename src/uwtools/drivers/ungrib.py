"""
A driver for the Ungrib model.
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


class Ungrib(Driver):
    """
    A driver for the Ungrib program.
    """

    _driver_name = STR.ungrib

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

    # Workflow tasks

    @task
    def gribfile_aaa(self):
        """
        The gribfile.
        """
        path = self._rundir / "GRIBFILE.AAA"
        yield self._taskname(path)
        yield asset(path, path.is_symlink)
        infile = Path(self._driver_config["gfs_file"])
        yield file(path=infile)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(infile)

    @task
    def namelist_wps(self):
        """
        The namelist file.
        """
        d = {
            "update_values": {
                "share": {
                    "end_date": self._cycle.strftime("%Y-%m-%d_%H:00:00"),
                    "interval_seconds": 1,
                    "max_dom": 1,
                    "start_date": self._cycle.strftime("%Y-%m-%d_%H:00:00"),
                    "wrf_core": "ARW",
                },
                "ungrib": {
                    "out_format": "WPS",
                    "prefix": "FILE",
                },
            }
        }
        path = self._rundir / "namelist.wps"
        yield self._taskname(path)
        yield asset(path, path.is_file)
        yield None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=d,
            path=path,
        )

    @tasks
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.gribfile_aaa(),
            self.namelist_wps(),
            self.runscript(),
            self.vtable(),
        ]

    @tasks
    def run(self):
        """
        A run.
        """
        yield self._taskname("run")
        yield (self._run_via_batch_submission() if self._batch else self._run_via_local_execution())

    @task
    def runscript(self):
        """
        The runscript.
        """
        path = self._runscript_path
        yield self._taskname(path.name)
        yield asset(path, path.is_file)
        yield None
        envcmds = self._driver_config.get("execution", {}).get("envcmds", [])
        execution = [self._runcmd, "test $? -eq 0 && touch %s/done" % self._rundir]
        scheduler = self._scheduler if self._batch else None
        path.parent.mkdir(parents=True, exist_ok=True)
        rs = self._runscript(envcmds=envcmds, execution=execution, scheduler=scheduler)
        with open(path, "w", encoding="utf-8") as f:
            print(rs, file=f)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)

    @task
    def vtable(self):
        """
        The Vtable.
        """
        path = self._rundir / "Vtable"
        yield self._taskname(path)
        yield asset(path, path.is_symlink)
        yield None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(Path(self._driver_config["vtable"]))

    # Private helper methods

    @property
    def _driver_config(self) -> Dict[str, Any]:
        """
        Returns the config block specific to this driver.
        """
        driver_config: Dict[str, Any] = self._config["ungrib"]
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
        return "%s Ungrib %s" % (self._cycle.strftime("%Y%m%d %HZ"), suffix)

    def _validate(self) -> None:
        """
        Perform all necessary schema validation.
        """
        for schema_name in ("ungrib", "platform"):
            self._validate_one(schema_name=schema_name)
