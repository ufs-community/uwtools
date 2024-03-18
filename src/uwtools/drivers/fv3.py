"""
A driver for the FV3 model.
"""

import os
import stat
from datetime import datetime
from pathlib import Path
from shutil import copy
from typing import Any, Dict

from iotaa import asset, dryrun, task, tasks

from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import Driver
from uwtools.logging import log
from uwtools.strings import STR
from uwtools.utils.tasks import filecopy, symlink


class FV3(Driver):
    """
    A driver for the FV3 model.
    """

    _driver_name = STR.fv3

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

    @tasks
    def boundary_files(self):
        """
        Lateral boundary-condition files.
        """
        yield self._taskname("lateral boundary-condition files")
        lbcs = self._driver_config["lateral_boundary_conditions"]
        offset = abs(lbcs["offset"])
        endhour = self._driver_config["length"] + offset + 1
        interval = lbcs["interval_hours"]
        symlinks = {}
        for n in [7] if self._driver_config["domain"] == "global" else range(1, 7):
            for boundary_hour in range(offset, endhour, interval):
                target = Path(lbcs["path"].format(tile=n, forecast_hour=boundary_hour))
                linkname = (
                    self._rundir / "INPUT" / f"gfs_bndy.tile{n}.{(boundary_hour - offset):03d}.nc"
                )
                symlinks[target] = linkname
        yield [symlink(target=t, linkname=l) for t, l in symlinks.items()]

    @task
    def diag_table(self):
        """
        The diag_table file.
        """
        fn = "diag_table"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield None
        if src := self._driver_config.get(fn):
            path.parent.mkdir(parents=True, exist_ok=True)
            copy(src=src, dst=path)
        else:
            log.warning("No '%s' defined in config", fn)

    @task
    def field_table(self):
        """
        The field_table file.
        """
        fn = "field_table"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield None
        self._create_user_updated_config(
            config_class=FieldTableConfig,
            config_values=self._driver_config["field_table"],
            path=path,
        )

    @tasks
    def files_copied(self):
        """
        Files copied for run.
        """
        yield self._taskname("files copied")
        yield [
            filecopy(src=Path(src), dst=self._rundir / dst)
            for dst, src in self._driver_config.get("files_to_copy", {}).items()
        ]

    @tasks
    def files_linked(self):
        """
        Files linked for run.
        """
        yield self._taskname("files linked")
        yield [
            symlink(target=Path(target), linkname=self._rundir / linkname)
            for linkname, target in self._driver_config.get("files_to_link", {}).items()
        ]

    @task
    def model_configure(self):
        """
        The model_configure file.
        """
        fn = "model_configure"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield None
        self._create_user_updated_config(
            config_class=YAMLConfig,
            config_values=self._driver_config["model_configure"],
            path=path,
        )

    @task
    def namelist_file(self):
        """
        The namelist file.
        """
        fn = "input.nml"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield None
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
            self.boundary_files(),
            self.diag_table(),
            self.field_table(),
            self.files_copied(),
            self.files_linked(),
            self.model_configure(),
            self.namelist_file(),
            self.restart_directory(),
            self.runscript(),
        ]

    @task
    def restart_directory(self):
        """
        The RESTART directory.
        """
        yield self._taskname("RESTART directory")
        path = self._rundir / "RESTART"
        yield asset(path, path.is_dir)
        yield None
        path.mkdir(parents=True)

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
            "ESMF_RUNTIME_COMPLIANCECHECK": "OFF:depth=4",
            "KMP_AFFINITY": "scatter",
            "MPI_TYPE_DEPTH": 20,
            "OMP_NUM_THREADS": self._driver_config.get("execution", {}).get("threads", 1),
            "OMP_STACKSIZE": "512m",
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

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s %s" % (self._cycle.strftime("%Y%m%d %HZ"), self._driver_name, suffix)

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
