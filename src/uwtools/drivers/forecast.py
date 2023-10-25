"""
Drivers for forecast models.
"""


import os
import sys
from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import datetime
from importlib import resources
from pathlib import Path
from typing import Dict, Optional

from uwtools.config.core import FieldTableConfig, NMLConfig, YAMLConfig
from uwtools.config.j2template import J2Template
from uwtools.drivers.driver import Driver
from uwtools.logging import log
from uwtools.scheduler import BatchScript
from uwtools.types import DefinitePath, OptionalPath
from uwtools.utils.file import writable
from uwtools.utils.processing import execute


class Forecast(Driver, ABC):
    """
    The base class for any forecast driver.
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
        bs = self.scheduler.batch_script
        bs.append(pre_run)
        bs.append(self.run_cmd())
        return bs

    def output(self) -> None:
        """
        ???
        """

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
        Runs the forecast either locally or via a batch-script submission.

        :param cycle: The date and start time for the forecast.
        :return: Did the model run exit with success status?
        """
        # Prepare directories.
        run_directory = Path(self._config["run_dir"])
        self.create_directory_structure(run_directory, "delete")

        self._prepare_config_files(cycle, Path(run_directory))

        self._config["cycle-dependent"].update(self._define_boundary_files())

        for file_category in ["static", "cycle-dependent"]:
            self.stage_files(run_directory, self._config[file_category], link_files=True)

        if self._batch_script is not None:
            batch_script = self.batch_script()
            outpath = Path(run_directory) / self._batch_script

            if self._dry_run:
                # Apply switch to allow user to view the run command of config.
                # This will not run the job.
                log.info("Batch Script:")
                batch_script.dump(None)
                return True

            batch_script.dump(outpath)
            return self.scheduler.submit_job(outpath)

        pre_run = self._mpi_env_variables(" ")
        full_cmd = f"{pre_run} {self.run_cmd()}"
        if self._dry_run:
            log.info("Would run: ")
            print(full_cmd, file=sys.stdout)
            return True

        result = execute(cmd=full_cmd, cwd=run_directory)
        return result.success

    # Private methods

    def _boundary_hours(self, lbcs_config: Dict) -> tuple[int, int, int]:
        """
        Prepares parameters to generate the lateral boundary condition (LBCS) forecast hours from an
        external intput data source, e.g. GFS, RAP, etc.

        :param lbcs_config: The section of the config file specifying the lateral boundary
            conditions settings.
        :return: The offset hours between the cycle and the external input data, the hours between
            LBC ingest, and the last hour of the external input data forecast
        """
        offset = abs(lbcs_config["offset"])
        end_hour = self._config["length"] + offset + 1
        return offset, lbcs_config["interval_hours"], end_hour

    @abstractmethod
    def _define_boundary_files(self) -> Dict[str, str]:
        """
        Sets the names of files used at boundary times that must be staged for a limited area
        forecast run.

        :return: A dict of boundary file names mapped to source input file paths
        """

    @abstractmethod
    def _mpi_env_variables(self, delimiter: str = " ") -> str:
        """
        Sets the environment variables needed for running the mpi command.

        :param delimiter: The delimiter to be used between items in the configuration dictionary.
        :return: A bash-formatted string of MPI environment variables.
        """

    @abstractmethod
    def _prepare_config_files(self, cycle: datetime, run_directory: DefinitePath) -> None:
        """
        Calls the methods for the set of configuration files neeed by the given model.

        :param cycle: The date and start time for the forecast.
        :param run_directory: Path of desired run directory.
        """


class FV3Forecast(Forecast):
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

    # Public methods

    @classmethod
    def create_directory_structure(
        cls, run_directory: DefinitePath, exist_act: str = "delete"
    ) -> None:
        """
        Creates the run directory and adds subdirectories INPUT and RESTART. Verifies creation of
        all directories.

        :param run_directory: Path of desired run directory.
        :param exist_act: Could be any of 'delete', 'rename', 'quit'. Sets how the program responds
            to a preexisting run directory. The default is to delete the old run directory.
        """
        run_directory = Path(run_directory)
        cls._create_run_directory(run_directory, exist_act)
        # Create the two required subdirectories.
        for subdir in ("INPUT", "RESTART"):
            path = run_directory / subdir
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

    def create_model_configure(self, cycle: datetime, output_path: OptionalPath) -> None:
        """
        Uses the forecast config object to create a model_configure.

        :param cycle: The date and start time for the forecast.
        :param output_path: Optional location of the output model_configure file.
        """
        self._create_user_updated_config(
            config_class=YAMLConfig,
            config_values=self._config.get("model_configure", {}),
            output_path=output_path,
        )
        start_time = cycle.strftime("%Y-%m-%d_%H:%M:%S")
        date_values = {
            "start_year": cycle.strftime("%Y"),
            "start_month": cycle.strftime("%m"),
            "start_day": cycle.strftime("%d"),
            "start_hour": cycle.strftime("%H"),
            "start_minute": cycle.strftime("%M"),
            "start_second": cycle.strftime("%S"),
        }
        log.info(f"Updating namelist date values to start at: {start_time}")
        config_obj = YAMLConfig(output_path)
        config_obj.update_values(date_values)
        config_obj.dump(output_path)

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

    @property
    def schema_file(self) -> Path:
        """
        The path to the file containing the schema to validate the config file against.

        :return: The string path to the schema file.
        """
        with resources.as_file(resources.files("uwtools.resources")) as path:
            return path / "FV3Forecast.jsonschema"

    # Private methods

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

    def _prepare_config_files(self, cycle: datetime, run_directory: DefinitePath) -> None:
        """
        Collect all the configuration files needed for FV3.

        :param cycle: The date and start time for the forecast.
        :param run_directory: Path of desired run directory.
        """
        run_directory = Path(run_directory)
        self.create_field_table(run_directory / "field_table")
        self.create_model_configure(cycle, run_directory / "model_configure")
        self.create_namelist(run_directory / "input.nml")

    def _mpi_env_variables(self, delimiter: str = " ") -> str:
        """
        Sets the environment variables needed for running the mpi command.

        :param delimiter: The delimiter to be used between items in the configuration dictionary.
        :return: A bash-formatted string of MPI environment variables.
        """
        envvars = {
            "KMP_AFFINITY": "scatter",
            "OMP_NUM_THREADS": self._config["runtime_info"].get("threads", 1),
            "OMP_STACKSIZE": "512m",
            "MPI_TYPE_DEPTH": 20,
            "ESMF_RUNTIME_COMPLIANCECHECK": "OFF:depth=4",
        }
        return delimiter.join([f"{k}={v}" for k, v in envvars.items()])


class MPASForecast(Forecast):
    """
    A Driver for the MPAS Atmosphere forecast model.
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

    def create_namelist(self, cycle: datetime, output_path: OptionalPath) -> None:
        """
        Uses an object with user supplied values and an optional namelist base file to create an
        output namelist file. Will "dereference" the base file.

        :param cycle: The date and start time for the forecast.
        :param output_path: Optional location of output namelist.
        """
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=self._config["namelist"],
            output_path=output_path,
        )
        start_time = cycle.strftime("%Y-%m-%d_%H:%M:%S")
        date_values = {
            "nhyd_model": {
                "config_start_time": start_time,
            },
        }
        log.info(f"Updating namelist date values to start at: {start_time}")
        config_obj = NMLConfig(output_path)
        config_obj.update_values(date_values)
        config_obj.dump(output_path)

    def create_streams(self, output_path: OptionalPath) -> None:
        """
        Create the streams file from a template.

        :param output_path: Optional location of output streams file.
        """

        template_file = self._config["streams"]["template"]
        values = self._config["streams"]["vars"]

        with open(template_file, "r", encoding="utf-8") as f:
            template_str = f.read()

        template = J2Template(values=values, template_str=template_str)
        with writable(output_path) as f:
            print(template.render(), file=f)

    @property
    def schema_file(self) -> Path:
        """
        The path to the file containing the schema to validate the config file against.

        :return: The string path to the schema file.
        """
        with resources.as_file(resources.files("uwtools.resources")) as path:
            return path / "MPASForecast.jsonschema"

    # Private methods

    def _define_boundary_files(self) -> Dict[str, str]:
        """
        No boundary files are currently needed for MPAS global support.

        :return: A dict of boundary file names mapped to source input file paths
        """
        return {}

    def _mpi_env_variables(self, delimiter=" ") -> str:
        """
        Sets the environment variables needed for running the mpi command.

        :param delimiter: The delimiter to be used between items in the configuration dictionary.
        :return: A bash-formatted string of MPI environment variables.
        """
        return delimiter.join([f"{k}={v}" for k, v in self._config.get("mpi_settings", {}).items()])

    def _prepare_config_files(self, cycle: datetime, run_directory: DefinitePath) -> None:
        """
        Collect all the configuration files needed for MPAS.

        :param cycle: The date and start time for the forecast.
        :param run_directory: Path of desired run directory.
        """
        run_directory = Path(run_directory)
        self.create_namelist(cycle, run_directory / "namelist.atmosphere")
        self.create_streams(run_directory / "streams.atmosphere")


CLASSES = {
    "FV3": FV3Forecast,
    "MPAS": MPASForecast,
}
