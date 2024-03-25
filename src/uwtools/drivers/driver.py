"""
An abstract class for component drivers.
"""
import os
import re
import stat
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Type

from iotaa import asset, task, tasks

from uwtools.config.formats.base import Config
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.validator import validate_internal
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.scheduler import JobScheduler
from uwtools.utils.processing import execute


class Driver(ABC):
    """
    An abstract class for component drivers.
    """

    def __init__(
        self,
        config: Optional[Path] = None,
        dry_run: bool = False,
        batch: bool = False,
        cycle: Optional[datetime] = None,
    ) -> None:
        """
        A component driver.

        :param config: Path to config file (read stdin if missing or None).
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        :param cycle: The cycle.
        """
        self._config = YAMLConfig(config=config)
        self._dry_run = dry_run
        self._batch = batch
        self._config.dereference()
        self._config.dereference(
            context={**({"cycle": cycle} if cycle else {}), **self._config.data}
        )
        self._validate()

    # Workflow tasks

    @tasks
    @abstractmethod
    def provisioned_run_directory(self):
        """
        Run directory provisioned with all required content.
        """

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
        path = self._rundir / "done"
        yield asset(path, path.is_file)
        yield self.provisioned_run_directory()
        cmd = "{x} >{x}.out 2>&1".format(x=self._runscript_path)
        execute(cmd=cmd, cwd=self._rundir, log_output=True)

    # Private helper methods

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

    @abstractmethod
    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """

    @property
    def _resources(self) -> Dict[str, Any]:
        """
        Returns configuration data for the runscript.
        """
        try:
            platform = self._config["platform"]
        except KeyError as e:
            raise UWConfigError("Required 'platform' block missing in config") from e
        return {
            "account": platform["account"],
            "rundir": self._rundir,
            "scheduler": platform["scheduler"],
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
    def _rundir(self) -> Path:
        """
        The path to the component's run directory.
        """
        return Path(self._driver_config["run_dir"])

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
            execution=["time %s" % self._runcmd, "test $? -eq 0 && touch %s/done" % self._rundir],
            scheduler=self._scheduler if self._batch else None,
        )
        with open(path, "w", encoding="utf-8") as f:
            print(rs, file=f)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
