"""
An abstract class for component drivers.
"""

import json
import os
import re
import stat
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Type, Union

from iotaa import asset, dryrun, external, task, tasks

from uwtools.config.formats.base import Config
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.validator import get_schema_file, validate, validate_internal
from uwtools.exceptions import UWConfigError, UWError
from uwtools.logging import log
from uwtools.scheduler import JobScheduler
from uwtools.utils.processing import execute


class Assets(ABC):
    """
    An abstract class to provision assets for component drivers.
    """

    def __init__(
        self,
        config: Optional[Union[dict, Path]],
        dry_run: bool = False,
        batch: bool = False,
        cycle: Optional[datetime] = None,
        leadtime: Optional[timedelta] = None,
        key_path: Optional[List[str]] = None,
    ) -> None:
        """
        A component driver.

        :param config: Path to config file (read stdin if missing or None).
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        :param cycle: The cycle.
        :param leadtime: The leadtime.
        :param key_path: Keys leading through the config to the driver's configuration block.
        """
        dryrun(enable=dry_run)
        self._config = YAMLConfig(config=config)
        self._batch = batch
        has_leadtime = leadtime is not None
        if has_leadtime and not cycle:
            raise UWError("When leadtime is specified, cycle is required")
        self._config.dereference(
            context={
                **({"cycle": cycle} if cycle else {}),
                **({"leadtime": leadtime} if has_leadtime else {}),
                **self._config.data,
            }
        )
        key_path = key_path or []
        for key in key_path:
            self._config = self._config[key]
        self._validate()

    # Workflow tasks

    @tasks
    @abstractmethod
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """

    @external
    def validate(self):
        """
        Validate the UW driver config.
        """
        yield self._taskname("valid schema")
        yield asset(None, lambda: True)

    # Private helper methods

    @staticmethod
    def _create_user_updated_config(
        config_class: Type[Config], config_values: dict, path: Path, schema: Optional[dict] = None
    ) -> None:
        """
        Create a config from a base file, user-provided values, or a combination of the two.

        :param config_class: The Config subclass matching the config type.
        :param config_values: The configuration object to update base values with.
        :param path: Path to dump file to.
        :param schema: Schema to validate final config against.
        """
        user_values = config_values.get("update_values", {})
        if base_file := config_values.get("base_file"):
            cfgobj = config_class(base_file)
            cfgobj.update_values(user_values)
            cfgobj.dereference()
            config = cfgobj.data
            dump = partial(cfgobj.dump, path)
        else:
            config = user_values
            dump = partial(config_class.dump_dict, config, path)
        if validate(schema=schema or {"type": "object"}, config=config):
            path.parent.mkdir(parents=True, exist_ok=True)
            dump()
            log.debug(f"Wrote config to {path}")
        else:
            log.debug(f"Failed to validate {path}")

    @property
    def _driver_config(self) -> Dict[str, Any]:
        """
        Returns the config block specific to this driver.
        """
        name = self._driver_name
        try:
            driver_config: Dict[str, Any] = self._config[name]
            return driver_config
        except KeyError as e:
            raise UWConfigError("Required '%s' block missing in config" % name) from e

    @property
    @abstractmethod
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """

    def _namelist_schema(
        self, config_keys: Optional[List[str]] = None, schema_keys: Optional[List[str]] = None
    ) -> dict:
        """
        Returns the (sub)schema for validating the driver's namelist content.

        :param config_keys: Keys leading to the namelist block in the driver config.
        :param schema_keys: Keys leading to the namelist-validating (sub)schema.
        """
        schema: dict = {"type": "object"}
        nmlcfg = self._driver_config
        for config_key in config_keys or ["namelist"]:
            nmlcfg = nmlcfg[config_key]
        if nmlcfg.get("validate", True):
            schema_file = get_schema_file(schema_name=self._driver_name.replace("_", "-"))
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)
            for schema_key in schema_keys or [
                "properties",
                self._driver_name,
                "properties",
                "namelist",
                "properties",
                "update_values",
            ]:
                schema = schema[schema_key]
        return schema

    @property
    def _rundir(self) -> Path:
        """
        The path to the component's run directory.
        """
        return Path(self._driver_config["run_dir"])

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s" % (self._driver_name, suffix)

    def _taskname_with_cycle(self, cycle: datetime, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s %s" % (cycle.strftime("%Y%m%d %HZ"), self._driver_name, suffix)

    def _taskname_with_cycle_and_leadtime(
        self, cycle: datetime, leadtime: timedelta, suffix: str
    ) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        return "%s %s %s" % (
            (cycle + leadtime).strftime("%Y%m%d %H:%M:%S"),
            self._driver_name,
            suffix,
        )

    def _validate(self) -> None:
        """
        Perform all necessary schema validation.
        """
        schema_name = self._driver_name.replace("_", "-")
        validate_internal(schema_name=schema_name, config=self._config)


class Driver(Assets):
    """
    An abstract class for standalone component drivers.
    """

    # Workflow tasks

    @tasks
    def run(self):
        """
        A run.
        """
        yield self._taskname("run")
        yield (self._run_via_batch_submission() if self._batch else self._run_via_local_execution())

    @task
    def _run_via_batch_submission(self):
        """
        A run executed via the batch system.
        """
        yield self._taskname("run via batch submission")
        path = Path("%s.submit" % self._runscript_path)
        yield asset(path, path.is_file)
        yield self.provisioned_run_directory()
        self._scheduler.submit_job(runscript=self._runscript_path, submit_file=path)

    @task
    def _run_via_local_execution(self):
        """
        A run executed directly on the local system.
        """
        yield self._taskname("run via local execution")
        path = self._rundir / self._runscript_done_file
        yield asset(path, path.is_file)
        yield self.provisioned_run_directory()
        cmd = "{x} >{x}.out 2>&1".format(x=self._runscript_path)
        execute(cmd=cmd, cwd=self._rundir, log_output=True)

    # Private helper methods

    @property
    def _resources(self) -> Dict[str, Any]:
        """
        Returns platform configuration data.
        """
        try:
            platform = self._config["platform"]
        except KeyError as e:
            raise UWConfigError("Required 'platform' block missing in config") from e
        return {
            "account": platform["account"],
            "rundir": self._rundir,
            "scheduler": platform["scheduler"],
            "stdout": "%s.out" % self._runscript_path.name,  # config may override
            **self._driver_config.get("execution", {}).get("batchargs", {}),
        }

    @property
    def _runcmd(self) -> str:
        """
        Returns the full command-line component invocation.
        """
        execution = self._driver_config.get("execution", {})
        mpiargs = execution.get("mpiargs", [])
        components = [
            execution.get("mpicmd"),  # MPI run program
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
    def _runscript_done_file(self):
        """
        The path to the done file produced by the successful completion of a run script.
        """
        return f"{self._runscript_path.name}.done"

    @property
    def _runscript_path(self) -> Path:
        """
        Returns the path to the runscript.
        """
        return self._rundir / f"runscript.{self._driver_name}"

    @property
    def _scheduler(self) -> JobScheduler:
        """
        Returns the job scheduler specified by the platform information.
        """
        return JobScheduler.get_scheduler(self._resources)

    def _validate(self) -> None:
        """
        Perform all necessary schema validation.
        """
        for schema_name in (self._driver_name.replace("_", "-"), "platform"):
            validate_internal(schema_name=schema_name, config=self._config)

    def _write_runscript(self, path: Path, envvars: Dict[str, str]) -> None:
        """
        Write the runscript.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        rs = self._runscript(
            envcmds=self._driver_config.get("execution", {}).get("envcmds", []),
            envvars=envvars,
            execution=[
                "time %s" % self._runcmd,
                "test $? -eq 0 && touch %s" % self._runscript_done_file,
            ],
            scheduler=self._scheduler if self._batch else None,
        )
        with open(path, "w", encoding="utf-8") as f:
            print(rs, file=f)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
