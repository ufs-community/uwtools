"""
A driver for the FV3 model.
"""

import os
import stat
from datetime import datetime
from pathlib import Path
from shutil import copy
from typing import Any, Dict, Optional

from iotaa import asset, dryrun, external, task, tasks

from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import Driver
from uwtools.logging import log
from uwtools.utils.file import resource_pathobj
from uwtools.utils.processing import execute


class FV3(Driver):
    """
    A driver for the FV3 model.
    """

    def __init__(
        self, config_file: Path, cycle: datetime, dry_run: bool = False, batch: bool = False
    ):
        """
        The FV3 driver.

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

    @tasks
    def boundary_files(self):
        """
        The FV3 lateral boundary-condition files.
        """
        yield self._taskname("lateral boundary condition files")
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
        yield [self._symlink(target=t, linkname=l) for t, l in symlinks.items()]

    @task
    def diag_table(self):
        """
        The FV3 diag_table file.
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
        The FV3 field_table file.
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
        Files copied for FV3 run.
        """
        yield self._taskname("files copied")
        yield [
            self._filecopy(src=Path(src), dst=self._rundir / dst)
            for dst, src in self._driver_config.get("files_to_copy", {}).items()
        ]

    @tasks
    def files_linked(self):
        """
        Files linked for FV3 run.
        """
        yield self._taskname("files linked")
        yield [
            self._symlink(target=Path(target), linkname=self._rundir / linkname)
            for linkname, target in self._driver_config.get("files_to_link", {}).items()
        ]

    @task
    def model_configure(self):
        """
        The FV3 model_configure file.
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
        The FV3 namelist file.
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
        The run directory provisioned with all required content.
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
        The FV3 RESTART directory.
        """
        yield self._taskname("RESTART directory")
        path = self._rundir / "RESTART"
        yield asset(path, path.is_dir)
        yield None
        path.mkdir(parents=True)

    @tasks
    def run(self):
        """
        FV3 run execution.
        """
        yield self._taskname("run")
        yield (self._run_via_batch_submission() if self._batch else self._run_via_local_execution())

    @task
    def runscript(self):
        """
        A runscript suitable for submission to the scheduler.
        """
        yield self._taskname("runscript")
        path = self._runscript_path
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

    # Private workflow tasks

    @external
    def _file(self, path: Path):
        """
        An existing file.

        :param path: Path to the file.
        """
        yield "File %s" % path
        yield asset(path, path.is_file)

    @task
    def _filecopy(self, src: Path, dst: Path):
        """
        A copy of an existing file.

        :param src: Path to the source file.
        :param dst: Path to the destination file to create.
        """
        yield "Copy %s -> %s" % (src, dst)
        yield asset(dst, dst.is_file)
        yield self._file(src)
        copy(src, dst)

    @task
    def _run_via_batch_submission(self):
        """
        FV3 run Execution via the batch system.
        """
        yield self._taskname("run via batch submission")
        path = Path("%s.submit" % self._runscript_path)
        yield asset(path, path.is_file)
        yield self.provisioned_run_directory()
        self._scheduler.submit_job(runscript=self._runscript_path, submit_file=path)

    @task
    def _run_via_local_execution(self):
        """
        FV3 run execution directly on the local system.
        """
        yield self._taskname("run via local execution")
        path = self._rundir / "done"
        yield asset(path, path.is_file)
        yield self.provisioned_run_directory()
        cmd = "{x} >{x}.out 2>&1".format(x=self._runscript_path)
        execute(cmd=cmd, cwd=self._rundir, log_output=True)

    @task
    def _symlink(self, target: Path, linkname: Path):
        """
        A symbolic link.

        :param target: The existing file or directory.
        :param linkname: The symlink to create.
        """
        yield "Link %s -> %s" % (linkname, target)
        yield asset(linkname, linkname.exists)
        yield self._file(target)
        linkname.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(src=target, dst=linkname)

    # Private helper methods

    @property
    def _driver_config(self) -> Dict[str, Any]:
        """
        Returns the config block specific to this driver.
        """
        driver_config: Dict[str, Any] = self._config["fv3"]
        return driver_config

    @property
    def _resources(self) -> Dict[str, Any]:
        """
        Returns configuration data for the FV3 runscript.
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
        return "%s FV3 %s" % (self._cycle.strftime("%Y%m%d %HZ"), suffix)

    def _validate(self) -> None:
        """
        Perform all necessary schema validation.
        """
        for schema_file in ("fv3.jsonschema", "platform.jsonschema"):
            self._validate_one(resource_pathobj(schema_file))
