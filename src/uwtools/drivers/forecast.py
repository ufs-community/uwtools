"""
Drivers for forecast models.
"""


import inspect
import logging
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from importlib import resources
from typing import Dict, Optional

from uwtools.drivers.driver import Driver
from uwtools.logger import Logger
from uwtools.scheduler import BatchScript, JobScheduler
from uwtools.utils import cli_helpers, file_helpers

from uwtools import config


class FV3Forecast(Driver):
    """
    A driver for the FV3 forecast model.
    """

    # Public methods

    def batch_script(self, job_resources: Mapping) -> BatchScript:
        """
        Write to disk, for submission to the batch scheduler, a script to run FV3.
        """
        return JobScheduler.get_scheduler(job_resources).batch_script

    @staticmethod
    def create_directory_structure(run_directory, exist_act="delete"):
        """
        Collects the name of the desired run directory, and has an optional flag for what to do if
        the run directory specified already exists. Creates the run directory and adds
        subdirectories INPUT and RESTART. Verifies creation of all directories.

        Args:
           run_directory: path of desired run directory
           exist_act: - could be any of 'delete', 'rename', 'quit'
                      - how program should act if run directory exists
                      - default is to delete old run directory
           Returns: None
        """

        # Caller should only provide correct argument.

        if exist_act not in ["delete", "rename", "quit"]:
            raise ValueError(f"Bad argument: {exist_act}")

        # Exit program with error if caller chooses to quit.

        if exist_act == "quit" and os.path.isdir(run_directory):
            logging.critical("User chose quit option when creating directory")
            sys.exit(1)

        # Delete or rename directory if it exists.

        file_helpers.handle_existing(run_directory, exist_act)

        # Create new run directory with two required subdirectories.

        for subdir in ("INPUT", "RESTART"):
            path = os.path.join(run_directory, subdir)
            logging.info("Creating directory: %s", path)
            os.makedirs(path)

    @staticmethod
    def create_field_table(update_obj, outfldtab_file, base_file=None):
        """
        Uses an object with user supplied values and an optional base file to create an output field
        table file. Will "dereference" the base file.

        Args:
            update_obj: in-memory dictionary initialized by object.
                        values override any settings in base file
            outfldtab_file: location of output field table
            base_file: optional path to file to use as a base file
        """
        if base_file:
            config_obj = config.FieldTableConfig(base_file)
            config_obj.update_values(update_obj)
            config_obj.dereference_all()
            config_obj.dump_file(outfldtab_file)
        else:
            # Dump update object to a Field Table file:
            config.FieldTableConfig.dump_file_from_dict(path=outfldtab_file, cfg=update_obj)

        msg = f"Namelist file {outfldtab_file} created"
        logging.info(msg)

    @staticmethod
    def create_namelist(update_obj, outnml_file, base_file=None):
        """
        Uses an object with user supplied values and an optional namelist base file to create an
        output namelist file. Will "dereference" the base file.

        Args:
            update_obj: in-memory dictionary initialized by object.
                        values override any settings in base file
            outnml_file: location of output namelist
            base_file: optional path to file to use as a base file
        """

        if base_file:
            config_obj = config.F90Config(base_file)
            config_obj.update_values(update_obj)
            config_obj.dereference_all()
            config_obj.dump_file(outnml_file)
        else:
            update_obj.dump_file(outnml_file)

        msg = f"Namelist file {outnml_file} created"
        logging.info(msg)

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
        Set up the formatting for the scheduler batch script.
        """
        # Add required fields to platform.
        # Currently supporting only slurm and none.
        slurmqueues = ["hera", "jet", "orion", "stampede"]
        if platform["queue"] is None and platform["machine"] in slurmqueues:
            platform["queue"] = "slurm"
        else:
            platform["queue"] = "none"

        return {
            "account": platform["account"],
            "nodes": 1,
            "queue": platform["queue"],
            "scheduler": platform["scheduler"],
            "tasks_per_node": 1,
            "walltime": "00:01:00",
        }

    def run(self, log: Optional[Logger] = None) -> None:
        """
        Runs FV3.
        """
        # Set up logging.
        if log is None:
            name = f"{inspect.stack()[0][3]}"
            log = cli_helpers.setup_logging(
                log_file="/dev/stdout",
                log_name=name,
                quiet=False,
                verbose=False,
            )
        # Read in the config file.
        forecast_config = config.YAMLConfig(self._config_file)

        # Define forecast model.
        forecast_model = forecast_config["forecast"]["EXTRN_MDL_NAME"]
        machine = forecast_config["platform"]["machine"]

        # Prepare directories.
        run_directory = forecast_config["forecast"]["FCSTDIR"]
        self.create_directory_structure(run_directory, "delete")

        static_files = forecast_config["forecast"]["STATIC"]
        self.stage_files(run_directory, static_files, link_files=False)
        cycledep_files = forecast_config["forecast"]["CYCLEDEP"]
        self.stage_files(run_directory, cycledep_files, link_files=True)

        # Create the job script.
        platform = {key: forecast_config["platform"][key] for key in forecast_config["platform"]}
        platform_resources = self.resources(platform)
        batch_script = self.batch_script(platform_resources)
        args = "--export=ALL -n"
        run_command = self.run_cmd(
            args,
            run_cmd=forecast_config["forecast"]["run_cmd"],
            exec_name=forecast_config["forecast"]["exec_name"],
        )

        if self._dry_run:
            # Apply switch to allow user to view the run command of config.
            # This will not run the job.
            log.info(f"Configuration: {forecast_model} {machine}")
            log.info(f"Run command: {run_command} {batch_script}")
            return

        # Run the job.
        if self._outfile is not None:
            outpath = run_directory.join(self._outfile)
            with open(outpath, "w", encoding="utf-8") as f:
                subprocess.run(
                    f"{run_command} {batch_script}",
                    stderr=subprocess.STDOUT,
                    check=False,
                    shell=True,
                    stdout=f,
                )
        else:
            subprocess.run(
                f"{run_command}",
                stderr=subprocess.STDOUT,
                check=False,
                shell=True,
            )

    def run_cmd(self, *args, run_cmd: str, exec_name: str) -> str:
        """
        Constructs the command to run FV3.
        """
        args_str = " ".join(str(arg) for arg in args)
        return f"{run_cmd} {args_str} {exec_name}"

    @property
    def schema_file(self) -> str:
        """
        The path to the file containing the schema to validate the config file against.
        """
        with resources.as_file(resources.files("uwtools.resources")) as path:
            return (path / "FV3Forecast.jsonschema").as_posix()

    @staticmethod
    def stage_files(
        run_directory: str, files_to_stage: Dict[str, str], link_files: bool = False
    ) -> None:
        """
        Takes in run directory and dictionary of file names and paths that need to be staged in the
        run directory.

        Creates dst file in run directory and copies or links contents from the src path provided.
        """

        os.makedirs(run_directory, exist_ok=True)
        for dst_fn, src_path in files_to_stage.items():
            dst_path = os.path.join(run_directory, dst_fn)
            if link_files:
                os.symlink(src_path, dst_path)
            else:
                shutil.copyfile(src_path, dst_path)
            msg = f"File {src_path} staged in run directory at {dst_fn}"
            logging.info(msg)

    # Private methods

    def _create_model_config(self, base_file: str, outconfig_file: str) -> None:
        """
        Collects all the user inputs required to create a model config file, calling the existing
        model config tools. This will be unique to the app being run and will appropriately parse
        subsequent stages of the workflow. Defaults will be filled in if not provided by the user.
        Equivalent references to config_default.yaml or config.community.yaml from SRW will need to
        be made for the other apps.

        Args:
            base_file: Path to base config file
            outconfig_file: Path to output configuration file
        """
        config.create_config_obj(
            input_base_file=base_file, config_file=self._config_file, outfile=outconfig_file
        )
        msg = f"Config file {outconfig_file} created"
        logging.info(msg)
