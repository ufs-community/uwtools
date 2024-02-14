"""
An abstract class for component drivers.
"""
import re
from abc import ABC, abstractmethod
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Type

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
        self._config.dereference()
        self._validate()
        self._dry_run = dry_run
        self._batch = batch

    @staticmethod
    def _create_user_updated_config(
        config_class: Type[Config], config_values: dict, path: Path
    ) -> None:
        """
        Create a config from a base file, user-provided values, or a combination of the two.

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
    def _driver_config(self) -> Dict[str, Any]:
        """
        Returns the config block specific to this driver.
        """

    @property
    @abstractmethod
    def _resources(self) -> Dict[str, Any]:
        """
        Returns configuration data for the FV3 runscript.
        """

    @property
    def _runcmd(self) -> str:
        """
        Returns the full command-line component invocation.
        """
        execution = self._driver_config.get("execution", {})
        mpiargs = execution.get("mpiargs", [])
        components = [
            execution["mpicmd"],  # MPI run program
            *[str(x) for x in mpiargs],  # MPI arguments
            execution["executable"],  # component executable name
        ]
        return " ".join(filter(None, components))

    def _runscript(
        self,
        execution: List[str],
        envcmds: Optional[List[str]] = None,
        envvars: Optional[Dict[str, str]] = None,
        scheduler: Optional[JobScheduler] = None,
    ) -> str:
        """
        Returns a driver runscript.

        :param execution: Statements to execute.
        :param envcmds: Shell commands to set up runtime environment.
        :param envvars: Environment variables to set in runtime environment.
        :param scheduler: A job-scheduler object.
        """
        # Render script sections into a template, remove any extraneous newlines related to elided
        # sections, then return the resulting string.
        template = """
        #!/bin/bash

        {directives}

        {envcmds}

        {envvars}

        {execution}
        """
        rs = dedent(template).format(
            directives="\n".join(scheduler.directives if scheduler else ""),
            envcmds="\n".join(envcmds or []),
            envvars="\n".join([f"export {k}={v}" for k, v in (envvars or {}).items()]),
            execution="\n".join(execution),
        )
        return re.sub(r"\n\n\n+", "\n\n", rs.strip())

    @property
    def _scheduler(self) -> JobScheduler:
        """
        Returns the job scheduler specified by the platform information.
        """
        return JobScheduler.get_scheduler(self._resources)

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
        log.info("Validating config per %s", schema_file)
        if not validator.validate_yaml(config=self._config, schema_file=schema_file):
            raise UWConfigError("YAML validation errors")
