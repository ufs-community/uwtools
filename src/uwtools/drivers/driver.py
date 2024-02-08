"""
Provides an abstract class representing drivers for various components.
"""

import os
import shutil
from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Dict, Type, Union

from iotaa import task

from uwtools.config import validator
from uwtools.config.formats.base import Config
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.scheduler import JobScheduler
from uwtools.types import DefinitePath, OptionalPath


class Driver(ABC):
    """
    An abstract class representing drivers for various components.
    """

    def __init__(
        self,
        config_file: DefinitePath,
        dry_run: bool = False,
        batch: bool = False,
    ):
        """
        Initialize the driver.
        """

        self._config_file = config_file
        self._dry_run = dry_run
        self._batch = batch
        self._validate()
        self._experiment_config = YAMLConfig(config=config_file)
        self._platform_config = self._experiment_config.get("platform", {})
        self._config: Dict[str, Any] = {}

    # Workflow methods

    @abstractmethod
    @task
    def run(self):
        """
        Run the component.
        """

    @abstractmethod
    @task
    def runscript(self):
        """
        A runscript suitable for submission to the scheduler.
        """

    # Public methods

    @abstractmethod
    def resources(self) -> Mapping:
        """
        Parses the config and returns a formatted dictionary for the runscript.
        """

    @property
    def scheduler(self) -> JobScheduler:
        """
        The job scheduler specified by the platform information.

        :return: The scheduler object
        """
        return JobScheduler.get_scheduler(self.resources())

    @property
    @abstractmethod
    def schema_file(self) -> Path:
        """
        The path to the file containing the schema to validate the config file against.
        """

    @staticmethod
    def stage_files(
        run_directory: Path,
        files_to_stage: Dict[str, Union[list, str]],
        link_files: bool = False,
        dry_run: bool = False,
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
            dst_path = run_directory / dst_rel_path
            if isinstance(src_path_or_paths, list):
                Driver.stage_files(
                    dst_path,
                    {os.path.basename(src): src for src in src_path_or_paths},
                    link_files,
                )
            else:
                if dry_run:
                    msg = f"File {src_path_or_paths} would be staged as {dst_path}"
                    log.info(msg)
                else:
                    msg = f"File {src_path_or_paths} staged as {dst_path}"
                    log.info(msg)
                    link_or_copy(src_path_or_paths, dst_path)  # type: ignore

    # Private methods

    @staticmethod
    def _create_user_updated_config(
        config_class: Type[Config], config_values: dict, output_path: OptionalPath
    ) -> None:
        """
        Create a config from a base file, user-provided values, of a combination of the two.

        :param config_class: The Config subclass matching the config type.
        :param config_values: The configuration object to update base values with.
        :param output_path: Optional path to dump file to.
        """
        user_values = config_values.get("update_values", {})
        if base_file := config_values.get("base_file"):
            config_obj = config_class(base_file)
            config_obj.update_values(user_values)
            config_obj.dereference()
            config_obj.dump(output_path)
        else:
            config_class.dump_dict(cfg=user_values, path=output_path)
        if output_path:
            log.info(f"Wrote config to {output_path}")

    def _run_cmd(self) -> str:
        """
        The full command-line component invocation.

        :return: String containing MPI command, MPI arguments, and exec name.
        """
        mpi_args = self._config.get("runtime_info", {}).get("mpi_args", [])
        components = [
            self._platform_config["mpicmd"],  # MPI run program
            *[str(x) for x in mpi_args],  # MPI arguments
            self._config["executable"],  # component executable name
        ]
        return " ".join(filter(None, components))

    def _validate(self) -> None:
        """
        Validate the user-supplied config file.

        :raises: UWConfigError if config fails validation.
        """
        if not validator.validate_yaml(config=self._config_file, schema_file=self.schema_file):
            raise UWConfigError("YAML validation errors")
