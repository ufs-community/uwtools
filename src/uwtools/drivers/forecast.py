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

from uwtools.config.core import FieldTableConfig, NMLConfig, realize_config
from uwtools.drivers.driver import Driver
from uwtools.scheduler import BatchScript, JobScheduler
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
        self._fcst_config = self._config["forecast"]

    # Public methods

    def batch_script(self, platform_resources: Mapping) -> BatchScript:
        """
        Write to disk, for submission to the batch scheduler, a script to run FV3.
        """
        return JobScheduler.get_scheduler(platform_resources).batch_script

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

        handle_existing(run_directory, exist_act)

        # Create new run directory with two required subdirectories.

        for subdir in ("INPUT", "RESTART"):
            path = os.path.join(run_directory, subdir)
            logging.info("Creating directory: %s", path)
            os.makedirs(path)

    @staticmethod
    def create_field_table(update_obj: dict, outfldtab_file, base_file=None):
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
            config_obj = FieldTableConfig(base_file)
            config_obj.update_values(update_obj)
            config_obj.dereference_all()
            config_obj.dump(outfldtab_file)
        else:
            # Dump update object to a Field Table file:
            FieldTableConfig.dump_dict(path=outfldtab_file, cfg=update_obj)

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
            config_obj = NMLConfig(base_file)
            config_obj.update_values(update_obj)
            config_obj.dereference_all()
            config_obj.dump(outnml_file)
        else:
            update_obj.dump(outnml_file)

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
        Parses the config and returns a formatted dictionary for the batch script.
        """

        return self._fcst_config["jobinfo"].update({
            "account": self._config["user"]["account"],
            "scheduler": self._config["platform"]["scheduler"],
        })

    def run(self, cdate, cyc) -> None:
        """
        Runs FV3 either as a subprocess or by submitting a batch script.
        """
        # Prepare directories.
        run_directory = self._fcst_config["run_dir"]
        self.create_directory_structure(run_directory, "delete")

        self._fcst_config["cycledep"].update(self._define_boundary_files())

        for file_category in ["static", "cycledep"]:
            self.stage_files(run_directory, file_category, link_files=True)

        run_command = self.run_cmd(
            args,
            run_cmd=self._platform_config["mpicmd"],
            exec_name=self._fcst_config["exec_name"],
        )

        if self._batch_script is not None:

            scheduler = JobScheduler.get_scheduler(platform_resources)
            batch_script = self._create_batch_script(scheduler)
            batch_script.append(run_command)

            if self._dry_run:

                # Apply switch to allow user to view the run command of config.
                # This will not run the job.
                logging.info("Batch Script:")
                logging.info(batch_script)
                return

            outpath = Path(run_directory) / self._batch_script
            scheduler.dump(outpath)
            scheduler.run_job(outputh)
            return

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

        link_or_copy = os.symlink if link_files else shutil.copyfile

        for dst_fn, src_path in files_to_stage.items():
            dst_path = os.path.join(run_directory, dst_fn)
            if isinstance(src_path, list):
                self.stage_files(
                    run_directory,
                    {os.path.join(dst_path, os.path.basename(src)): src
                        for src in src_path},
                    link_files,
                    )
                continue
            link_or_copy(src_path, dst_path)
            msg = f"File {src_path} staged in run directory at {dst_fn}"
            logging.info(msg)

    # Private methods

    def _create_batch_script(self, scheduler: JobScheduler) -> BatchScript:

        """
        Setup a batch script with a run command.
        """
        return scheduler.batch_script.append(run_command)


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
        realize_config(
            input_file=base_file,
            input_format=FORMAT.yaml,
            output_file=outconfig_file,
            output_format=FORMAT.yaml,
            values_file=self._config_file,
            values_format=FORMAT.yaml,
        )
        msg = f"Config file {outconfig_file} created"
        logging.info(msg)

    def _define_boundary_files(self, length_category) -> Dict:

        """
        Maps the prepared boundary conditions to the appropriate
        hours for the forecast.
        """

        cycledep_boundary_files = {}
        boudary_file_template = lbcs_config["output_file_template"]
        lbcs_config = self._config["preprocessing"]["lateral_boundary_conditions"]
        offset = abs(lbcs_config["offset"])
        end_hour = self._fcst_config["length"][length_category] + offset + 1
        boundary_hours = range(
            offset,
            lbcs_config["interval_hours"],
            end_hour,
            )
        for tile in self._fcst_config["tiles"]:
            for boundary_hour in boundary_hours:
                fhr = boundary_hour - offset
                link_name = f"gfs_bndy.tile{tile}.{fhr}.nc"
                boundary_file_path = boudary_file_template.format(tile=tile, fhr=boundary_hour)

                cycledep_boundary_files.update(
                    {link_name: boundary_file_path}
                    )

        return cycledep_boundary_files




CLASSES = {"FV3": FV3Forecast}
