"""
An abstract class for component drivers.
"""
import os
import re
import shutil
from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Type, Union

from uwtools.config import validator
from uwtools.config.formats.base import Config
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.scheduler import JobScheduler
from uwtools.types import DefinitePath


class Driver(ABC):
    """
    An abstract class for component drivers.
    """

    def __init__(self, config_file: DefinitePath, dry_run: bool = False, batch: bool = False):
        """
        A component driver.

        :param config_file: Path to config file.
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        """
        self._config = YAMLConfig(config=config_file)
        self._validate()
        self._dry_run = dry_run
        self._batch = batch

    @property
    @abstractmethod
    def _driver_config(self) -> Dict[str, Any]:
        """
        Returns the config block specific to this driver.
        """

    @staticmethod
    def _create_user_updated_config(
        config_class: Type[Config], config_values: dict, path: Path
    ) -> None:
        """
        Create a config from a base file, user-provided values, of a combination of the two.

        :param config_class: The Config subclass matching the config type.
        :param config_values: The configuration object to update base values with.
        :param path: Path to dump file to.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        user_values = config_values.get("update_values", {})
        if base_file := config_values.get("base_file"):
            config_obj = config_class(base_file)
            config_obj.update_values(user_values)
            config_obj.dereference()
            config_obj.dump(path)
        else:
            config_class.dump_dict(cfg=user_values, path=path)
        log.debug(f"Wrote config to {path}")

    @property
    @abstractmethod
    def _resources(self) -> Mapping:
        """
        Configuration data for FV3 runscript.

        :return: A formatted dictionary needed to create a runscript
        """

    @property
    def _run_cmd(self) -> str:
        """
        The full command-line component invocation.

        :return: String containing MPI command, MPI arguments, and exec name.
        """
        execution = self._driver_config.get("execution", {})
        mpi_args = execution.get("mpi_args", [])
        components = [
            self._config["platform"]["mpicmd"],  # MPI run program
            *[str(x) for x in mpi_args],  # MPI arguments
            execution["executable"],  # component executable name
        ]
        return " ".join(filter(None, components))

    def _runscript(
        self,
        envvars: Dict[str, str],
        execution: List[str],
        scheduler: Optional[JobScheduler] = None,
    ) -> str:
        """
        Returns a driver runscript.

        :param envvars: Environment variables to set before execution.
        :param execution: Statements to execute. :scheduler: A job-scheduler instance.
        """
        template = """
        #!/bin/bash

        {directives}

        {envvars}

        {execution}
        """
        rs = dedent(template).format(
            directives="\n".join(sorted(scheduler.directives) if scheduler else ""),
            envvars="\n".join([f"{k}={v}" for k, v in envvars.items()]),
            execution="\n".join(execution),
        )
        return re.sub(r"\n\n\n+", "\n\n", rs.strip())

    @property
    def _scheduler(self) -> JobScheduler:
        """
        The job scheduler specified by the platform information.

        :return: The scheduler object
        """
        return JobScheduler.get_scheduler(self._resources)

    @staticmethod
    def _stage_files(
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
                Driver._stage_files(
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

    @abstractmethod
    def _validate(self) -> None:
        """
        Perform all necessary schema validation.
        """

    def _validate_one(self, schema_file: Path) -> None:
        """
        Validate the config.

        :param schema_file: The schema file to validate the config against.
        :raises: UWConfigError if config fails validation.
        """
        if not validator.validate_yaml(config=self._config, schema_file=schema_file):
            raise UWConfigError("YAML validation errors")
