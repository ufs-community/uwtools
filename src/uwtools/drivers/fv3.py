"""
FV3 driver.
"""

import os
import stat
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Dict

from iotaa import asset, refs, task, tasks

from uwtools.config.formats.fieldtable import FieldTableConfig
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.drivers.driver import Driver
from uwtools.logging import log
from uwtools.types import DefinitePath, OptionalPath
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

    # Workflow methods

    @task
    def field_table(self):
        """
        An FV3 field_table file.
        """
        fn = "field_table"
        yield "%s FV3 %s" % (self._cyclestr, fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield self.run_directory()
        self._create_user_updated_config(
            config_class=FieldTableConfig,
            config_values=self._config["field_table"],
            output_path=path,
        )

    @task
    def model_configure(self):
        """
        An FV3 model_configure file.
        """
        fn = "model_configure"
        yield "%s FV3 %s" % (self._cyclestr, fn)
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield self.run_directory()
        self._create_user_updated_config(
            config_class=YAMLConfig,
            config_values=self._config["model_configure"],
            output_path=path,
        )

    @tasks
    def provisioned_run_directory(self):
        """
        A run directory provisioned with all required content.
        """
        yield "%s FV3 provisioned run directory" % self._cyclestr
        yield [self.runscript(), self.field_table(), self.model_configure()]

    @tasks
    def run(self):
        """
        Execution of the run.
        """
        yield "%s FV3 run" % self._cyclestr
        yield (self.run_via_batch_submission() if self._batch else self.run_via_local_execution())

    @task
    def run_directory(self):
        """
        The run directory.
        """
        yield "%s FV3 run directory" % self._cyclestr
        path = self._rundir
        yield asset(path, path.is_dir)
        yield None
        path.mkdir(parents=True)

    @task
    def run_via_batch_submission(self):
        """
        Execution of the run via the batch system.
        """
        yield "%s FV3 run via batch submission" % self._cyclestr
        path = self._rundir / ("%s.submit" % self._runscript_name)
        yield asset(path, path.is_file)
        deps = self.provisioned_run_directory()
        yield deps
        self.scheduler.submit_job(runscript=refs(deps)[0], submit_file=path)

    @task
    def run_via_local_execution(self):
        """
        Execution of the run directly on the local system.
        """
        yield "%s FV3 run via local execution" % self._cyclestr
        path = self._rundir / "done"
        yield asset(path, path.is_file)
        deps = self.provisioned_run_directory()
        yield deps
        runscript = refs(deps)[0].name
        cmd = f"./{runscript} >{runscript}.out 2>&1"
        execute(cmd=cmd, cwd=self._rundir, log_output=True)

    @task
    def runscript(self):
        """
        A runscript suitable for submission to the scheduler.
        """
        yield "%s FV3 runscript" % self._cyclestr
        path = self._rundir / self._runscript_name
        yield asset(path, path.is_file)
        yield self.run_directory()
        bs = self.scheduler.runscript
        bs.append(self._mpi_env_variables("\n"))
        bs.append(self.run_cmd())
        bs.append("touch %s/done" % self._rundir)
        bs.dump(path)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)

    # Public methods

    def create_namelist(self, output_path: OptionalPath) -> None:
        """
        Uses an object with user supplied values and an optional namelist base file to create an
        output namelist file. Will "dereference" the base file.

        :param output_path: Optional location of output namelist.
        """
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self._config.get("namelist", {}),
            output_path=output_path,
        )

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
        self._prepare_config_files(self._rundir)
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
        Parses the experiment configuration to provide the information needed for the runscript.

        :return: A formatted dictionary needed to create a runscript
        """

        return {
            "account": self._experiment_config["platform"]["account"],
            "rundir": self._rundir,
            "scheduler": self._experiment_config["platform"]["scheduler"],
            **self._config["jobinfo"],
        }

    @property
    def schema_file(self) -> Path:
        """
        The path to the file containing the schema to validate the config file against.
        """
        return resource_pathobj("fv3.jsonschema")

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
            "OMP_NUM_THREADS": self._config.get("runtime_info", {}).get("threads", 1),
            "OMP_STACKSIZE": "512m",
            "MPI_TYPE_DEPTH": 20,
            "ESMF_RUNTIME_COMPLIANCECHECK": "OFF:depth=4",
        }
        return delimiter.join([f"{k}={v}" for k, v in envvars.items()])

    def _prepare_config_files(self, run_directory: Path) -> None:
        """
        Collect all the configuration files needed for FV3.
        """
        if self._dry_run:
            for call in ("field_table", "model_configure", "input.nml"):
                log.info(f"Would prepare: {run_directory}/{call}")
        else:
            # self.create_field_table(run_directory / "field_table")
            # self.create_model_configure(run_directory / "model_configure")
            self.create_namelist(run_directory / "input.nml")

    @property
    def _runscript_name(self) -> str:
        """
        Returns the name of the runscript.
        """
        return "runscript"
