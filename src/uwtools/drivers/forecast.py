"""
Drivers for forecast models.
"""


import os
import sys
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from uwtools.config.core import FieldTableConfig, NMLConfig, YAMLConfig
from uwtools.drivers.driver import Driver
from uwtools.logging import log
from uwtools.scheduler import BatchScript
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import handle_existing, resource_pathobj
from uwtools.utils.processing import execute


class FV3Forecast(Driver):
    """
    A driver for the FV3 forecast model.
    """

    def __init__(
        self,
        config_file: str,
        dry_run: bool = False,
        batch_script: Optional[str] = None,
    ):
        """
        Initialize the Forecast Driver.
        """

        super().__init__(config_file=config_file, dry_run=dry_run, batch_script=batch_script)
        self._config = self._experiment_config["forecast"]

    # Public methods

    def batch_script(self) -> BatchScript:
        """
        Prepare batch script contents for interaction with system scheduler.

        :return: The batch script object with all run commands needed for executing the program.
        """
        pre_run = self._mpi_env_variables("\n")
        batch_script = self.scheduler.batch_script
        batch_script.append(pre_run)
        batch_script.append(self.run_cmd())
        return batch_script

    @staticmethod
    def create_directory_structure(
        run_directory: DefinitePath, exist_act: str = "delete", dry_run: bool = False
    ) -> None:
        """
        Collects the name of the desired run directory, and has an optional flag for what to do if
        the run directory specified already exists. Creates the run directory and adds
        subdirectories INPUT and RESTART. Verifies creation of all directories.

        :param run_directory: Path of desired run directory.
        :param exist_act: Could be any of 'delete', 'rename', 'quit'. Sets how the program responds
            to a preexisting run directory. The default is to delete the old run directory.
        """

        run_directory = Path(run_directory)

        # Caller should only provide correct argument.

        if exist_act not in ["delete", "rename", "quit"]:
            raise ValueError(f"Bad argument: {exist_act}")

        # Exit program with error if caller chooses to quit.

        if exist_act == "quit" and run_directory.is_dir():
            log.critical("User chose quit option when creating directory")
            sys.exit(1)

        # Delete or rename directory if it exists.

        if dry_run and run_directory.is_dir():
            log.info(f"Would {exist_act} directory")
        else:
            handle_existing(str(run_directory), exist_act)

        # Create new run directory with two required subdirectories.

        for subdir in ("INPUT", "RESTART"):
            path = run_directory / subdir
            if dry_run:
                log.info("Would create directory: %s", path)
            else:
                log.info("Creating directory: %s", path)
                os.makedirs(path)

    def create_field_table(self, output_path: OptionalPath) -> None:
        """
        Uses the forecast config object to create a Field Table.

        :param output_path: Optional location of output field table.
        """
        self._create_user_updated_config(
            config_class=FieldTableConfig,
            config_values=self._config.get("field_table", {}),
            output_path=output_path,
        )

    def create_model_configure(self, output_path: OptionalPath) -> None:
        """
        Uses the forecast config object to create a model_configure.

        :param output_path: Optional location of the output model_configure file.
        """
        self._create_user_updated_config(
            config_class=YAMLConfig,
            config_values=self._config.get("model_configure", {}),
            output_path=output_path,
        )

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

    def output(self) -> None:
        """
        ???
        """

    def prepare_directories(self) -> Path:
        """
        Prepares the run directory and stages static and cycle-dependent files.
        """
        run_directory = self._config["run_dir"]
        self.create_directory_structure(run_directory, "delete", dry_run=self._dry_run)

        self._prepare_config_files(Path(run_directory))

        self._config["cycle-dependent"].update(self._define_boundary_files())

        for file_category in ["static", "cycle-dependent"]:
            self.stage_files(
                run_directory, self._config[file_category], link_files=True, dry_run=self._dry_run
            )
        return run_directory

    def requirements(self) -> None:
        """
        ???
        """

    def resources(self) -> Mapping:
        """
        Parses the experiment configuration to provide the information needed for the batch script.

        :return: A formatted dictionary needed to create a batch script
        """

        return {
            "account": self._experiment_config["user"]["account"],
            "scheduler": self._experiment_config["platform"]["scheduler"],
            **self._config["jobinfo"],
        }

    def run(self, cycle: datetime) -> bool:
        """
        Runs FV3 either locally or via a batch-script submission.

        :return: Did the FV3 run exit with success status?
        """
        status, output = (
            self._run_via_batch_submission()
            if self._batch_script
            else self._run_via_local_execution()
        )
        if self._dry_run:
            for line in output:
                log.info(line)
        return status

    @property
    def schema_file(self) -> Path:
        """
        The path to the file containing the schema to validate the config file against.
        """
        return resource_pathobj("FV3Forecast.jsonschema")

    # Private methods

    def _boundary_hours(self, lbcs_config: Dict) -> tuple[int, int, int]:
        """
        Prepares parameters to generate the lateral boundary condition (LBCS) forecast hours from an
        external intput data source, e.g. GFS, RAP, etc.

        :return: The offset hours between the cycle and the external input data, the hours between
            LBC ingest, and the last hour of the external input data forecast
        """
        offset = abs(lbcs_config["offset"])
        end_hour = self._config["length"] + offset + 1
        return offset, lbcs_config["interval_hours"], end_hour

    def _define_boundary_files(self) -> Dict[str, str]:
        """
        Maps the prepared boundary conditions to the appropriate hours for the forecast.

        :return: A dict of boundary file names mapped to source input file paths
        """
        boundary_files = {}
        lbcs_config = self._experiment_config["preprocessing"]["lateral_boundary_conditions"]
        boundary_file_template = lbcs_config["output_file_template"]
        offset, interval, endhour = self._boundary_hours(lbcs_config)
        for tile in self._config["tiles"]:
            for boundary_hour in range(offset, endhour, interval):
                forecast_hour = boundary_hour - offset
                link_name = f"INPUT/gfs_bndy.tile{tile}.{forecast_hour:03d}.nc"
                boundary_file_path = boundary_file_template.format(
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
            "OMP_NUM_THREADS": self._config["runtime_info"].get("threads", 1),
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
            self.create_field_table(run_directory / "field_table")
            self.create_model_configure(run_directory / "model_configure")
            self.create_namelist(run_directory / "input.nml")

    def _run_via_batch_submission(self) -> Tuple[bool, List[str]]:
        """
        Prepares and submits a batch script.

        :return: A tuple that contains a boolean of success status of the FV3 run and a list of
            strings that make up the batch script.
        """
        run_directory = self.prepare_directories()
        batch_script = self.batch_script()
        batch_lines = ["Batch script:", *str(batch_script).split("\n")]
        if self._dry_run:
            return True, batch_lines

        assert self._batch_script is not None
        outpath = run_directory / self._batch_script

        batch_script.dump(outpath)
        return self.scheduler.submit_job(outpath), batch_lines

    def _run_via_local_execution(self) -> Tuple[bool, List[str]]:
        """
        Collects the necessary MPI environment variables in order to construct full run command,
        then executes said command.

        :return: A tuple containing a boolean of the success status of the FV3 run and a list of
            strings that make up the full command line.
        """
        pre_run = self._mpi_env_variables(" ")
        full_cmd = f"{pre_run} {self.run_cmd()}"
        command_lines = ["Command:", *full_cmd.split("\n")]
        if self._dry_run:
            return True, command_lines
        result = execute(cmd=full_cmd)
        return result.success, command_lines


CLASSES = {"FV3": FV3Forecast}
