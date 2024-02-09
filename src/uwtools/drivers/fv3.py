"""
FV3 driver.
"""

import os
import stat
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from shutil import copyfile

from iotaa import asset, external, task, tasks

from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import Driver
from uwtools.logging import log
from uwtools.types import DefinitePath
from uwtools.utils.file import resource_pathobj
from uwtools.utils.processing import execute


class FV3(Driver):
    """
    A driver for the FV3 model.
    """

    def __init__(
        self,
        config_file: DefinitePath,
        cycle: datetime,
        dry_run: bool = False,
        batch: bool = False,
    ):
        """
        Initialize the driver.
        """

        super().__init__(config_file=config_file, dry_run=dry_run, batch=batch)
        self._cycle = cycle
        self._config = self._experiment_config["fv3"]
        self._rundir = Path(self._config["run_dir"])

    # Public workflow tasks

    @tasks
    def boundary_files(self):
        """
        The FV3 lateral boundary-condition files.
        """
        yield self._taskname("lateral boundary condition files")
        lbcs = self._experiment_config["preprocessing"]["lateral_boundary_conditions"]
        offset = abs(lbcs["offset"])
        endhour = self._config["length"] + offset + 1
        interval = lbcs["interval_hours"]
        symlinks = {}
        for n in [7] if self._config["domain"] == "global" else range(1, 7):
            for bndyhour in range(offset, endhour, interval):
                target = Path(lbcs["output_file_path"].format(tile=n, forecast_hour=bndyhour))
                linkname = self._rundir / "INPUT" / f"gfs_bndy.tile{n}.{(bndyhour - offset):03d}.nc"
                symlinks[target] = linkname
        yield [self._symlink(target, linkname) for target, linkname in symlinks.items()]

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
        if src := self._config.get(fn):
            path.parent.mkdir(parents=True, exist_ok=True)
            copyfile(src=src, dst=path)
        else:
            log.warn("No %s defined in config", fn)

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
            config_values=self._config["field_table"],
            path=path,
        )

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
            config_values=self._config["model_configure"],
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
            config_values=self._config.get("namelist", {}),
            path=path,
        )

    @tasks
    def provisioned_run_directory(self):
        """
        The run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.diag_table(),
            self.field_table(),
            self.model_configure(),
            self.namelist_file(),
            self.runscript(),
        ]

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
        path.parent.mkdir(parents=True, exist_ok=True)
        bs = self._scheduler.runscript
        bs.append(self._mpi_env_variables("\n"))
        bs.append(self._run_cmd())
        bs.append("touch %s/done" % self._rundir)
        bs.dump(path)
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
        cmd = "./{x} >{x}.out 2>&1".format(x=self._runscript_path)
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

    # Public methods

    # def prepare_directories(self) -> Path:
    #     """
    #     Prepares the run directory and stages static and cycle-dependent files.

    #     :return: Path to the run directory.
    #     """
    #     self._config["cycle_dependent"].update(self._define_boundary_files())
    #     for file_category in ["static", "cycle_dependent"]:
    #         self._stage_files(
    #             self._rundir,
    #             self._config[file_category],
    #             link_files=True,
    #             dry_run=self._dry_run,
    #         )
    #     return self._rundir

    # Private methods

    def _mpi_env_variables(self, delimiter: str = " ") -> str:
        """
        Set the environment variables needed for the MPI job.

        :return: A bash string of environment variables
        """
        envvars = {
            "ESMF_RUNTIME_COMPLIANCECHECK": "OFF:depth=4",
            "KMP_AFFINITY": "scatter",
            "MPI_TYPE_DEPTH": 20,
            "OMP_NUM_THREADS": self._config.get("execution", {}).get("threads", 1),
            "OMP_STACKSIZE": "512m",
        }
        return delimiter.join([f"{k}={v}" for k, v in envvars.items()])

    def _resources(self) -> Mapping:
        """
        Configuration data for FV3 runscript.

        :return: A formatted dictionary needed to create a runscript
        """
        return {
            "account": self._experiment_config["platform"]["account"],
            "rundir": self._rundir,
            "scheduler": self._experiment_config["platform"]["scheduler"],
            **self._config.get("execution", {}).get("batch_args", {}),
        }

    @property
    def _runscript_path(self) -> Path:
        """
        Returns the path to the runscript.
        """
        return self._rundir / "runscript"

    @property
    def _schema_file(self) -> Path:
        """
        The path to the file containing the schema to validate the config file against.
        """
        return resource_pathobj("fv3.jsonschema")

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s FV3 %s" % (self._cycle.strftime("%Y%m%d %HZ"), suffix)
