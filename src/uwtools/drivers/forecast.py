"""
Drivers for forecast models.
"""


import logging
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from functools import cached_property
from importlib import resources
from pathlib import Path
from typing import Dict

from uwtools.config.core import Config, FieldTableConfig, NMLConfig, realize_config, YAMLConfig
from uwtools.drivers.driver import Driver
from uwtools.scheduler import BatchScript, JobScheduler
from uwtools.types import OptionalPath
from uwtools.utils.file import FORMAT, handle_existing


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
        Initialize the Forecast Driver
        """

        super().__init__()
        self._config = self._experiment_config["forecast"]

    # Public methods

    def batch_script(self) -> BatchScript:
        """
        Write to disk, for submission to the batch scheduler, a script to run FV3.
        """
        pre_run = self._mpi_env_variables("\n")
        return self.scheduler.batch_script.append(pre_run).append(self.run_cmd())

    @staticmethod
    def create_directory_structure(run_directory, exist_act="delete"):
        """
        Collects the name of the desired run directory, and has an optional flag for what to do if
        the run directory specified already exists. Creates the run directory and adds
        subdirectories INPUT and RESTART. Verifies creation of all directories.

        :param run_directory: path of desired run directory
        :param exist_act: - could be any of 'delete', 'rename', 'quit'
                      - how program should act if run directory exists
                      - default is to delete old run directory
        """

        # Caller should only provide correct argument.

        if exist_act not in ["delete", "rename", "quit"]:
            raise ValueError(f"Bad argument: {exist_act}")

        # Exit program with error if caller chooses to quit.

        if exist_act == "quit" and os.path.isdir(run_directory):
            logging.critical("User chose quit option when creating directory")
            sys.exit(1)

        # Delete or rename directory if it exists.

        handle_existing(run_directory, exist_act)

        # Create new run directory with two required subdirectories.

        for subdir in ("INPUT", "RESTART"):
            path = os.path.join(run_directory, subdir)
            logging.info("Creating directory: %s", path)
            os.makedirs(path)

    def create_field_table(self, output_path: OptionalPath) -> None:
        """
        Uses the forecast config object to create a Field Table

        :param output_path: optional location of output field table
        """
        self._create_user_updated_config(
                config_class=FieldTableConfig,
                config_values=self._config["field_table"],
                output_path=output_path,
                )


    def create_model_configure(self, output_path: OptionalPath) -> None:
        """
        Uses the forecast config object to create a model_configure

        :param output_path: optional location of the output model_configure file
        """
        self._create_user_updated_config(
                config_class=YAMLConfig,
                config_values=self._config["model_configure"],
                output_path=output_path,
                )

    def create_namelist(self, output_path: OptionalPath) -> None:
        """
        Uses an object with user supplied values and an optional namelist base file to create an
        output namelist file. Will "dereference" the base file.

        :param output_path: optional location of output namelist
        """
        self._create_user_updated_config(
                config_class=NMLConfig,
                config_values=self._config["namelist"],
                output_path=output_path,
                )


    def output(self) -> None:
        """
        ???
        """

    def requirements(self) -> None:
        """
        ???
        """

    def resources(self, platform: dict) -> Mapping:
        """
        Parses the config and returns a formatted dictionary for the batch script.
        """

        return self._config["jobinfo"].update({
            "account": self._experiment_config["user"]["account"],
            "scheduler": self._experiment_config["platform"]["scheduler"],
        })

    def run(self, cdate, cyc) -> None:
        """
        Runs FV3 either as a subprocess or by submitting a batch script.
        """
        # Prepare directories.
        run_directory = self._config["run_dir"]
        self.create_directory_structure(run_directory, "delete")

        self._config["cycledep"].update(self._define_boundary_files())

        for file_category in ["static", "cycledep"]:
            self.stage_files(run_directory, file_category, link_files=True)

        if self._batch_script is not None:

            batch_script = self.batch_script

            if self._dry_run:

                # Apply switch to allow user to view the run command of config.
                # This will not run the job.
                logging.info("Batch Script:")
                logging.info(batch_script)
                return

            outpath = Path(run_directory) / self._batch_script
            batch_script.dump(outpath)
            self.scheduler.run_job(outpath)
            return

        if self._dry_run:
            logging.info("Would run: ")
            logging.info(self.run_cmd())
            return

        subprocess.run(
            f"{self.run_cmd()}",
            stderr=subprocess.STDOUT,
            check=False,
            shell=True,
        )

    @property
    def schema_file(self) -> str:
        """
        The path to the file containing the schema to validate the config file against.
        """
        with resources.as_file(resources.files("uwtools.resources")) as path:
            return (path / "FV3Forecast.jsonschema").as_posix()

    # Private methods

    def _define_boundary_files(self) -> Dict:
        """
        Maps the prepared boundary conditions to the appropriate
        hours for the forecast.
        """

        cycledep_boundary_files = {}
        lbcs_config = self._experiment_config["preprocessing"]["lateral_boundary_conditions"]
        boudary_file_template = lbcs_config["output_file_template"]
        offset = abs(lbcs_config["offset"])
        end_hour = self._config["length"] + offset + 1
        boundary_hours = range(
            offset,
            lbcs_config["interval_hours"],
            end_hour,
            )
        for tile in self._config["tiles"]:
            for boundary_hour in boundary_hours:
                fhr = boundary_hour - offset
                link_name = f"gfs_bndy.tile{tile}.{fhr}.nc"
                boundary_file_path = boudary_file_template.format(tile=tile, fhr=boundary_hour)

                cycledep_boundary_files.update(
                    {link_name: boundary_file_path}
                    )

        return cycledep_boundary_files


    def _mpi_env_variables(self, delimiter=" "):
        """
        Returns a bash string of environment variables needed to run the
        MPI job.
        """
        envvars = {
            "KMP_AFFINITY": "scatter",
            "OMP_NUM_THREADS": self._config["jobinfo"].get("threads", 1),
            "OMP_STACKSIZE": self._config["jobinfo"].get("threads", "512m"),
            "MPI_TYPE_DEPTH": 20,
            "ESMF_RUNTIME_COMPLIANCECHECK": "OFF:depth=4",
        }
        return delimiter.join([f"{k=v}" for k, v in envvars.items()])



CLASSES = {"FV3": FV3Forecast}
