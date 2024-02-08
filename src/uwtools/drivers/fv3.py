"""
FV3 driver.
"""

import os
import stat
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from shutil import copyfile
from typing import Dict

from iotaa import asset, task, tasks

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

    @task
    def diag_table(self):
        """
        The FV3 diag_table file.
        """
        fn = "diag_table"
        yield self._taskname(fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield self._run_directory()
        if src := self._config.get(fn):
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
        yield self._run_directory()
        self._create_user_updated_config(
            config_class=FieldTableConfig,
            config_values=self._config["field_table"],
            output_path=path,
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
        yield self._run_directory()
        self._create_user_updated_config(
            config_class=YAMLConfig,
            config_values=self._config["model_configure"],
            output_path=path,
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
        yield self._run_directory()
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self._config.get("namelist", {}),
            output_path=path,
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
        yield self._run_directory()
        bs = self.scheduler.runscript
        bs.append(self._mpi_env_variables("\n"))
        bs.append(self._run_cmd())
        bs.append("touch %s/done" % self._rundir)
        bs.dump(path)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)

    # Private workflow tasks

    @task
    def _run_directory(self):
        """
        The run directory, initially empty.
        """
        yield self._taskname("run directory")
        path = self._rundir
        yield asset(path, path.is_dir)
        yield None
        path.mkdir(parents=True)

    @task
    def _run_via_batch_submission(self):
        """
        FV3 run Execution via the batch system.
        """
        yield self._taskname("run via batch submission")
        path = Path("%s.submit" % self._runscript_path)
        yield asset(path, path.is_file)
        yield self.provisioned_run_directory()
        self.scheduler.submit_job(runscript=self._runscript_path, submit_file=path)

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

    # Public methods

    # def create_directory_structure(self) -> None:
    #     run_directory = Path(Path(self._config["run_dir"]))
    #     for subdir in ("INPUT", "RESTART"):
    #         path = run_directory / subdir
    #         log.info("Creating directory: %s", path)
    #         path.mkdir(parents=True)

    def prepare_directories(self) -> Path:
        """
        Prepares the run directory and stages static and cycle-dependent files.

        :return: Path to the run directory.
        """
        # self.create_directory_structure(run_directory, ExistAct.delete, dry_run=self._dry_run)
        # self._prepare_config_files(self._rundir)
        self._config["cycle_dependent"].update(self._define_boundary_files())
        for file_category in ["static", "cycle_dependent"]:
            self.stage_files(
                self._rundir,
                self._config[file_category],
                link_files=True,
                dry_run=self._dry_run,
            )
        return self._rundir

    def resources(self) -> Mapping:
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

    # Private methods

    def _boundary_hours(self, lbcs_config: Dict) -> tuple[int, int, int]:
        """
        Prepares parameters to generate the lateral boundary condition (LBCS) forecast hours from an
        external input data source, e.g. GFS, RAP, etc.

        :return: The offset hours between the cycle and the external input data, the hours between
            LBC ingest, and the last hour of the external input data forecast
        """
        offset = abs(lbcs_config["offset"])
        end_hour = self._config["length"] + offset + 1
        return offset, lbcs_config["interval_hours"], end_hour

    @property
    def _cyclestr(self) -> str:
        """
        Returns a formatted-for-logging representation of the forecast cycle.
        """
        return self._cycle.strftime("%Y%m%d %HZ")

    def _define_boundary_files(self) -> Dict[str, str]:
        """
        Maps the prepared boundary conditions to the appropriate hours for the forecast.

        :return: A dict of boundary file names mapped to source input file paths
        """
        boundary_files = {}
        lbcs_config = self._experiment_config["preprocessing"]["lateral_boundary_conditions"]
        boundary_file_path = lbcs_config["output_file_path"]
        offset, interval, endhour = self._boundary_hours(lbcs_config)
        tiles = [7] if self._config["domain"] == "global" else range(1, 7)
        for tile in tiles:
            for boundary_hour in range(offset, endhour, interval):
                forecast_hour = boundary_hour - offset
                link_name = f"INPUT/gfs_bndy.tile{tile}.{forecast_hour:03d}.nc"
                boundary_file_path = boundary_file_path.format(
                    tile=tile,
                    forecast_hour=boundary_hour,
                )
                boundary_files[link_name] = boundary_file_path

        return boundary_files

    def _mpi_env_variables(self, delimiter: str = " ") -> str:
        """
        Set the environment variables needed for the MPI job.

        :return: A bash string of environment variables
        """
        envvars = {
            "KMP_AFFINITY": "scatter",
            "OMP_NUM_THREADS": self._config.get("execution", {}).get("threads", 1),
            "OMP_STACKSIZE": "512m",
            "MPI_TYPE_DEPTH": 20,
            "ESMF_RUNTIME_COMPLIANCECHECK": "OFF:depth=4",
        }
        return delimiter.join([f"{k}={v}" for k, v in envvars.items()])

    # def _prepare_config_files(self, run_directory: Path) -> None:
    #     """
    #     Collect all the configuration files needed for FV3.
    #     """
    #     if self._dry_run:
    #         for call in ("field_table", "model_configure", "input.nml"):
    #             log.info(f"Would prepare: {run_directory}/{call}")
    #     else:
    #         # self.create_field_table(run_directory / "field_table")
    #         # self.create_model_configure(run_directory / "model_configure")
    #         self.create_namelist(run_directory / "input.nml")

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
        return "%s FV3 %s" % (self._cyclestr, suffix)
