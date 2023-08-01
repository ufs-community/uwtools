"""
This file contains the forecast drivers for a variety of apps and physics suites.
"""

import logging
import os
import shutil
import sys
from importlib import resources
from typing import Dict

from uwtools import config
from uwtools.drivers.driver import Driver
from uwtools.utils import file_helpers


class FV3Forecast(Driver):
    """
    Concrete class to handle UFS Short Range Weather app forecasts.

    FV3 (ATM-only) mode.
    """

    def __init__(self):
        """
        Initialize the Forecast driver.
        """
        with resources.as_file(resources.files("uwtools.resources")) as path:
            self.schema = (path / "FV3Forecast.jsonschema").as_posix()
        super().__init__()

    @property
    def schema(self):
        """
        The schema to validate the config file against.
        """
        return self.schema

    def requirements(self):
        """
        Recursively parse config and platform files to determine and fill in any dependencies.
        """

    def resources(self):
        """
        Determine necessary task objects and fill in resource requirements of each.

        Returns a Config object containing the HPC resources needed.
        """

    def create_model_config(self, base_file: str, config_file: str, outconfig_file: str) -> None:
        """
        Collects all the user inputs required to create a model config file, calling the existing
        model config tools. This will be unique to the app being run and will appropriately parse
        subsequent stages of the workflow. Defaults will be filled in if not provided by the user.
        Equivalent references to config_default.yaml or config.community.yaml from SRW will need to
        be made for the other apps.

        Args:
            base_file: Path to base config file
            config_file: Path to user configuration file
            outconfig_file: Path to output configuration file
        """
        config.create_config_obj(
            input_base_file=base_file, config_file=config_file, outfile=outconfig_file
        )
        msg = f"Config file {outconfig_file} created"
        logging.info(msg)

    def create_namelist(self, update_obj, outnml_file, base_file=None):
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

    def create_field_table(self, update_obj, outfldtab_file, base_file=None):
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

    def create_directory_structure(self, run_directory, exist_act="delete"):
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
            raise ValueError("Bad argument to create_directory_structure")

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

    def output(self):
        """
        Create list of SRW output files and stage them in the working directory.
        """

    def job_card(self):
        """
        Turns the resources config object into a batch card for the configured Task.
        """

    def run_cmd(self, *args, run_cmd: str, exec_name: str) -> str:
        """
        Constructs a command to be used to run the forecast executable.
        """
        args_str = " ".join(str(arg) for arg in args)
        return f"{run_cmd} {args_str} {exec_name}"

    def run(self):
        """
        Runs the forecast executable with the namelist file and staged input files.

        This will take in the executable built in run_cmd and then run it.
        """

    def stage_static_files(self, run_directory: str, static_files: Dict[str, str]) -> None:
        """
        Takes in run directory and dictionary of file names and paths that need to be staged in the
        run directory.

        Creates dst file in run directory and copies contents from the src path provided.
        """

        os.makedirs(run_directory, exist_ok=True)
        for dst_fn, src_path in static_files.items():
            dst_path = os.path.join(run_directory, dst_fn)
            shutil.copyfile(src_path, dst_path)
            msg = f"File {src_path} staged in run directory at {dst_fn}"
            logging.info(msg)
