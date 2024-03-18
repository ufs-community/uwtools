"""
A driver for the Ungrib model.
"""

import os
import stat
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from iotaa import asset, dryrun, external, run, task, tasks

from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import Driver
from uwtools.strings import STR
from uwtools.utils.processing import execute


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
    def initial_conditions(self):
        """
        Initial conditions.
        """
        fn = str(self._cycle)
        yield self._taskname(fn)
        path = self._rundir / fn
        taskname = "Initial conditions in %s" % self._rundir
        yield asset(path, path.is_file)
        yield [self.gribfile_aaa, self.namelist_wps, self.vtable]
        run(taskname, "ungrib 2>&1 | tee ungrib.out", cwd=path.parent)

    @task
    def gfs_local(self):
        """
        Doc string.
        """

    @external
    def gfs_upstream(self):
        """
        Doc string.
        """

    @task
    def gribfile_aaa(self):
        """
        The gribfile.
        """
        fn = "GRIBFILE.AAA"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        g = self.gfs_local
        yield g
        # path.symlink_to(Path(refs(g).name))

    @task
    def namelist_wps(self):
        """
        The namelist file.
        """
        fn = "namelist.wps"
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
            # self.gribfile_aaa(),
            # self.namelist_wps(),
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
        yield asset(path, path.exists)
        yield None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        # path.symlink_to(Path(self._wpsfile))

    # Private workflow tasks

    @task
    def _run_via_batch_submission(self):
        """
        A run executed via the batch system.
        """
        yield self._taskname("run via batch submission")
        path = Path("%s.submit" % self._runscript_path)
        yield asset(path, path.is_file)
        yield self.provisioned_run_directory()
        self._scheduler.submit_job(runscript=self._runscript_path, submit_file=path)

    @task
    def _run_via_local_execution(self):
        """
        A run executed directly on the local system.
        """
        yield self._taskname("run via local execution")
        path = self._rundir / "done"
        yield asset(path, path.is_file)
        yield self.provisioned_run_directory()
        cmd = "{x} >{x}.out 2>&1".format(x=self._runscript_path)
        execute(cmd=cmd, cwd=self._rundir, log_output=True)

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

    def _wpsfile(self, fn: str) -> Path:
        return Path(os.environ["WPSFILES"]) / fn
