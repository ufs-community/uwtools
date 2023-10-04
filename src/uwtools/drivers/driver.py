"""
Provides an abstract class representing drivers for various NWP tools.
"""

import logging
import os
import shutil
from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Dict, Optional, Type, Union

from uwtools.config import validator
from uwtools.config.core import Config, YAMLConfig
from uwtools.scheduler import BatchScript, JobScheduler
from uwtools.types import OptionalPath


class Driver(ABC):
    """
    An abstract class representing drivers for various NWP tools.
    """

    def __init__(
        self,
        config_file: str,
        dry_run: bool = False,
        batch_script: Optional[str] = None,
    ):
        """
        Initialize the driver.
        """

        self._config_file = config_file
        self._dry_run = dry_run
        self._batch_script = batch_script
        self._validate()
        self._experiment_config = YAMLConfig(config_file=config_file)
        self._platform_config = self._experiment_config.get("platform", {})
        self._config_data: Dict[str, Any] = {}

    # Public methods

    @abstractmethod
    def batch_script(self) -> BatchScript:
        """
        Create a script for submission to the batch scheduler.
        """

    @abstractmethod
    def output(self) -> None:
        """
        ???
        """

    @abstractmethod
    def requirements(self) -> None:
        """
        ???
        """

    @abstractmethod
    def resources(self) -> Mapping:
        """
        Parses the config and returns a formatted dictionary for the batch script.
        """

    @abstractmethod
    def run(self, cycle: datetime) -> bool:
        """
        Run the NWP tool.

        :param cycle: The time stamp of the cycle to run.
        """

    def run_cmd(self) -> str:
        """
        The command-line command to run the NWP tool.
        """
        run_cmd = self._platform_config["mpicmd"]
        exec_name = self._config["exec_name"]
        run_time_args = self._config["runtime_info"].get("mpi_args", [])
        args_str = " ".join(str(arg) for arg in run_time_args)
        return f"{run_cmd} {args_str} {exec_name}"

    @property
    def scheduler(self) -> JobScheduler:
        """
        The job scheduler speficied by the platform information.
        """
        return JobScheduler.get_scheduler(self.resources())

    @property
    @abstractmethod
    def schema_file(self) -> str:
        """
        The path to the file containing the schema to validate the config file against.
        """

    @staticmethod
    def stage_files(
        run_directory: str, files_to_stage: Dict[str, Union[list, str]], link_files: bool = False
    ) -> None:
        """
        Creates destination files in run directory and copies or links contents from the source path
        provided. Source paths could be provided as a single path or a list of paths to be staged in
        a common directory.

        :param run_directory: Path of desired run directory.
        :param files_to_stage: File names in the run directory (keys) and their source paths
            (values).
        :param link_files: Whether to link or copy the files.
        """
        link_or_copy = os.symlink if link_files else shutil.copyfile
        for dst_rel_path, src_path_or_paths in files_to_stage.items():
            dst_path = os.path.join(run_directory, dst_rel_path)
            if isinstance(src_path_or_paths, list):
                Driver.stage_files(
                    dst_path,
                    {os.path.basename(src): src for src in src_path_or_paths},
                    link_files,
                )
            else:
                link_or_copy(src_path_or_paths, dst_path)  # type: ignore
                msg = f"File {src_path_or_paths} staged as {dst_path}"
                logging.info(msg)

    # Private methods

    @property
    def _config(self) -> Mapping:
        """
        The config object that describes the subset of an experiment config related to a subclass of
        Driver.
        """
        return self._config_data

    @_config.deleter
    def _config(self) -> None:
        """
        Deleter for _config.
        """
        self._config_data = {}

    @_config.setter
    def _config(self, config_obj: Dict[str, Any]) -> None:
        """
        Setter for _config.
        """
        self._config_data = config_obj

    @staticmethod
    def _create_user_updated_config(
        config_class: Type[Config], config_values: dict, output_path: OptionalPath
    ) -> None:
        """
        The standard procedure for updating a file of a configuration class type with user-provided
        values.

        :param config_class: the Config subclass matching the configure file type
        :param config_values: the in-memory configuration object to update base values with
        :param output_path: optional path to dump file to
        """

        # User-supplied values that override any settings in the base
        # file.
        user_values = config_values.get("update_values", {})

        if base_file := config_values.get("base_file"):
            config_obj = config_class(base_file)
            config_obj.update_values(user_values)
            config_obj.dereference_all()
            config_obj.dump(output_path)
        else:
            config_class.dump_dict(path=output_path, cfg=user_values)

        msg = f"Configure file {output_path} created"
        logging.info(msg)

    def _validate(self) -> bool:
        """
        Validate the user-supplied config file.
        """
        return validator.validate_yaml(
            config_file=self._config_file,
            schema_file=self.schema_file,
        )
