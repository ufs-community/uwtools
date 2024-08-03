"""
Abstract classes for component drivers.
"""

import json
import os
import re
import stat
from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime, timedelta
from functools import partial
from pathlib import Path
from textwrap import dedent
from typing import Any, Optional, Union

from iotaa import asset, dryrun, external, task, tasks

from uwtools.config.formats.base import Config
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.tools import walk_key_path
from uwtools.config.validator import get_schema_file, validate, validate_external, validate_internal
from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.scheduler import JobScheduler
from uwtools.strings import STR
from uwtools.utils.file import writable
from uwtools.utils.processing import execute

# NB: Class docstrings are programmatically defined.


class Assets(ABC):
    """
    An abstract class to provision assets for component drivers.
    """

    def __init__(
        self,
        cycle: Optional[datetime] = None,
        leadtime: Optional[timedelta] = None,
        config: Optional[Union[dict, str, YAMLConfig, Path]] = None,
        dry_run: bool = False,
        key_path: Optional[list[str]] = None,
        schema_file: Optional[Path] = None,
        controller: Optional[str] = None,
    ) -> None:
        config = config if isinstance(config, YAMLConfig) else YAMLConfig(config=config)
        config.dereference(
            context={
                **({STR.cycle: cycle} if cycle else {}),
                **({STR.leadtime: leadtime} if leadtime is not None else {}),
                **config.data,
            }
        )
        # The _config_full attribute points to the config block that includes the driver-specific
        # block and any surrounding context, including e.g. platform: for some drivers.
        self._config_full, _ = walk_key_path(config.data, key_path or [])
        # The _config attribute points to the driver-specific config block. It is supplemented with
        # config data from the controller block, if specified.
        try:
            self._config = self._config_full[self._driver_name]
        except KeyError as e:
            raise UWConfigError("Required '%s' block missing in config" % self._driver_name) from e
        if controller:
            self._config[STR.rundir] = self._config_full[controller][STR.rundir]
        self._validate(schema_file)
        dryrun(enable=dry_run)

    def __repr__(self) -> str:
        cycle = self._cycle.strftime("%Y-%m-%dT%H:%M") if hasattr(self, "_cycle") else None
        leadtime = None
        if hasattr(self, "_leadtime"):
            h, r = divmod(self._leadtime.total_seconds(), 3600)
            m, s = divmod(r, 60)
            leadtime = "%02d:%02d:%02d" % (h, m, s)
        return " ".join(filter(None, [str(self), cycle, leadtime, "in", self.config[STR.rundir]]))

    def __str__(self) -> str:
        return self._driver_name

    @property
    def config(self) -> dict:
        """
        A copy of the driver-specific config block.
        """
        return deepcopy(self._config)

    @property
    def config_full(self) -> dict:
        """
        A copy of the driver-specific config block's parent block.
        """
        return deepcopy(self._config_full)

    @property
    def rundir(self) -> Path:
        """
        The path to the component's run directory.
        """
        return Path(self.config[STR.rundir])

    # Workflow tasks

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
        config_class: type[Config], config_values: dict, path: Path, schema: Optional[dict] = None
    ) -> None:
        """
        Create a config from a base file, user-provided values, or a combination of the two.

        :param config_class: The Config subclass matching the config type.
        :param config_values: The configuration object to update base values with.
        :param path: Path to dump file to.
        :param schema: Schema to validate final config against.
        """
        user_values = config_values.get(STR.updatevalues, {})
        if base_file := config_values.get(STR.basefile):
            cfgobj = config_class(base_file)
            cfgobj.update_values(user_values)
            cfgobj.dereference()
            config = cfgobj.data
            dump = partial(cfgobj.dump, path)
        else:
            config = user_values
            dump = partial(config_class.dump_dict, config, path)
        if validate(schema=schema or {"type": "object"}, config=config):
            dump()
            log.debug(f"Wrote config to {path}")
        else:
            log.debug(f"Failed to validate {path}")

    @property
    @abstractmethod
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """

    def _namelist_schema(
        self, config_keys: Optional[list[str]] = None, schema_keys: Optional[list[str]] = None
    ) -> dict:
        """
        Returns the (sub)schema for validating the driver's namelist content.

        :param config_keys: Keys leading to the namelist block in the driver config.
        :param schema_keys: Keys leading to the namelist-validating (sub)schema.
        """
        schema: dict = {"type": "object"}
        nmlcfg = self.config
        for config_key in config_keys or [STR.namelist]:
            nmlcfg = nmlcfg[config_key]
        if nmlcfg.get(STR.validate, True):
            schema_file = get_schema_file(schema_name=self._driver_name.replace("_", "-"))
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)
            for schema_key in schema_keys or [
                STR.properties,
                self._driver_name,
                STR.properties,
                STR.namelist,
                STR.properties,
                STR.updatevalues,
            ]:
                schema = schema[schema_key]
        return schema

    def _taskname(self, suffix: str) -> str:
        """
        Returns a common tag for graph-task log messages.

        :param suffix: Log-string suffix.
        """
        cycle = getattr(self, "_cycle", None)
        leadtime = getattr(self, "_leadtime", None)
        timestr = (
            (cycle + leadtime).strftime("%Y%m%d %H:%M:%S")
            if cycle and leadtime is not None
            else cycle.strftime("%Y%m%d %HZ") if cycle else None
        )
        return " ".join(filter(None, [timestr, self._driver_name, suffix]))

    def _validate(self, schema_file: Optional[Path] = None) -> None:
        """
        Perform all necessary schema validation.

        :param schema_file: The JSON Schema file to use for validation.
        :raises: UWConfigError if config fails validation.
        """
        if schema_file:
            validate_external(schema_file=schema_file, config=self.config_full)
        else:
            validate_internal(
                schema_name=self._driver_name.replace("_", "-"), config=self.config_full
            )


class AssetsCycleBased(Assets):
    """
    An abstract class to provision assets for cycle-based components.
    """

    def __init__(
        self,
        cycle: datetime,
        config: Optional[Union[dict, str, YAMLConfig, Path]] = None,
        dry_run: bool = False,
        key_path: Optional[list[str]] = None,
        schema_file: Optional[Path] = None,
        controller: Optional[str] = None,
    ):
        super().__init__(
            cycle=cycle,
            config=config,
            dry_run=dry_run,
            key_path=key_path,
            schema_file=schema_file,
            controller=controller,
        )
        self._cycle = cycle

    @property
    def cycle(self):
        """
        The cycle.
        """
        return self._cycle


class AssetsCycleLeadtimeBased(Assets):
    """
    An abstract class to provision assets for cycle-and-leadtime-based components.
    """

    def __init__(
        self,
        cycle: datetime,
        leadtime: timedelta,
        config: Optional[Union[dict, str, YAMLConfig, Path]] = None,
        dry_run: bool = False,
        key_path: Optional[list[str]] = None,
        schema_file: Optional[Path] = None,
        controller: Optional[str] = None,
    ):
        super().__init__(
            cycle=cycle,
            leadtime=leadtime,
            config=config,
            dry_run=dry_run,
            key_path=key_path,
            schema_file=schema_file,
            controller=controller,
        )
        self._cycle = cycle
        self._leadtime = leadtime

    @property
    def cycle(self):
        """
        The cycle.
        """
        return self._cycle

    @property
    def leadtime(self):
        """
        The leadtime.
        """
        return self._leadtime


class AssetsTimeInvariant(Assets):
    """
    An abstract class to provision assets for time-invariant components.
    """

    def __init__(
        self,
        config: Optional[Union[dict, str, YAMLConfig, Path]] = None,
        dry_run: bool = False,
        key_path: Optional[list[str]] = None,
        schema_file: Optional[Path] = None,
        controller: Optional[str] = None,
    ):
        super().__init__(
            config=config,
            dry_run=dry_run,
            key_path=key_path,
            schema_file=schema_file,
            controller=controller,
        )


class Driver(Assets):
    """
    An abstract class for standalone component drivers.
    """

    def __init__(
        self,
        cycle: Optional[datetime] = None,
        leadtime: Optional[timedelta] = None,
        config: Optional[Union[dict, str, YAMLConfig, Path]] = None,
        dry_run: bool = False,
        key_path: Optional[list[str]] = None,
        batch: bool = False,
        schema_file: Optional[Path] = None,
        controller: Optional[str] = None,
    ):
        super().__init__(
            cycle=cycle,
            leadtime=leadtime,
            config=config,
            dry_run=dry_run,
            key_path=key_path,
            schema_file=schema_file,
            controller=controller,
        )
        self._batch = batch
        if controller:
            self._config[STR.execution] = self._config_full[controller][STR.execution]

    # Workflow tasks

    @tasks
    @abstractmethod
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """

    @tasks
    def run(self):
        """
        A run.
        """
        yield self._taskname(STR.run)
        yield (self._run_via_batch_submission() if self._batch else self._run_via_local_execution())

    @task
    def runscript(self):
        """
        The runscript.
        """
        path = self._runscript_path
        yield self._taskname(path.name)
        yield asset(path, path.is_file)
        yield None
        self._write_runscript(path)

    @task
    def _run_via_batch_submission(self):
        """
        A run executed via the batch system.
        """
        yield self._taskname("run via batch submission")
        path = Path("%s.submit" % self._runscript_path)
        yield asset(path, path.is_file)
        yield self.provisioned_rundir()
        self._scheduler.submit_job(runscript=self._runscript_path, submit_file=path)

    @task
    def _run_via_local_execution(self):
        """
        A run executed directly on the local system.
        """
        yield self._taskname("run via local execution")
        path = self.rundir / self._runscript_done_file
        yield asset(path, path.is_file)
        yield self.provisioned_rundir()
        cmd = "{x} >{x}.out 2>&1".format(x=self._runscript_path)
        execute(cmd=cmd, cwd=self.rundir, log_output=True)

    # Private helper methods

    @property
    def _run_resources(self) -> dict[str, Any]:
        """
        Returns platform configuration data.
        """
        try:
            platform = self.config_full[STR.platform]
        except KeyError as e:
            raise UWConfigError("Required 'platform' block missing in config") from e
        threads = self.config.get(STR.execution, {}).get(STR.threads)
        return {
            STR.account: platform[STR.account],
            STR.rundir: self.rundir,
            STR.scheduler: platform[STR.scheduler],
            STR.stdout: "%s.out" % self._runscript_path.name,  # config may override
            **({STR.threads: threads} if threads else {}),
            **self.config.get(STR.execution, {}).get(STR.batchargs, {}),
        }

    @property
    def _runcmd(self) -> str:
        """
        Returns the full command-line component invocation.
        """
        execution = self.config.get(STR.execution, {})
        mpiargs = execution.get(STR.mpiargs, [])
        components = [
            execution.get(STR.mpicmd),  # MPI run program
            *[str(x) for x in mpiargs],  # MPI arguments
            execution[STR.executable],  # component executable name
        ]
        return " ".join(filter(None, components))

    def _runscript(
        self,
        execution: list[str],
        envcmds: Optional[list[str]] = None,
        envvars: Optional[dict[str, str]] = None,
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
        return self.rundir / f"runscript.{self._driver_name}"

    @property
    def _scheduler(self) -> JobScheduler:
        """
        Returns the job scheduler specified by the platform information.
        """
        return JobScheduler.get_scheduler(self._run_resources)

    def _validate(self, schema_file: Optional[Path] = None) -> None:
        """
        Perform all necessary schema validation.

        :param schema_file: The JSON Schema file to use for validation.
        :raises: UWConfigError if config fails validation.
        """
        if schema_file:
            validate_external(schema_file=schema_file, config=self.config_full)
        else:
            validate_internal(
                schema_name=self._driver_name.replace("_", "-"), config=self.config_full
            )
        validate_internal(schema_name=STR.platform, config=self.config_full)

    def _write_runscript(self, path: Path, envvars: Optional[dict[str, str]] = None) -> None:
        """
        Write the runscript.
        """
        envvars = envvars or {}
        threads = self.config.get(STR.execution, {}).get(STR.threads)
        if threads and "OMP_NUM_THREADS" not in envvars:
            raise UWConfigError("Config specified threads but driver does not set OMP_NUM_THREADS")
        rs = self._runscript(
            envcmds=self.config.get(STR.execution, {}).get(STR.envcmds, []),
            envvars=envvars,
            execution=[
                "time %s" % self._runcmd,
                "test $? -eq 0 && touch %s" % self._runscript_done_file,
            ],
            scheduler=self._scheduler if self._batch else None,
        )
        with writable(path) as f:
            print(rs, file=f)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)


class DriverCycleBased(Driver):
    """
    An abstract class for standalone cycle-based component drivers.
    """

    def __init__(
        self,
        cycle: datetime,
        config: Optional[Union[dict, str, YAMLConfig, Path]] = None,
        dry_run: bool = False,
        key_path: Optional[list[str]] = None,
        batch: bool = False,
        schema_file: Optional[Path] = None,
        controller: Optional[str] = None,
    ):
        super().__init__(
            cycle=cycle,
            config=config,
            dry_run=dry_run,
            key_path=key_path,
            batch=batch,
            schema_file=schema_file,
            controller=controller,
        )
        self._cycle = cycle

    @property
    def cycle(self):
        """
        The cycle.
        """
        return self._cycle


class DriverCycleLeadtimeBased(Driver):
    """
    An abstract class for standalone cycle-and-leadtime-based component drivers.
    """

    def __init__(
        self,
        cycle: datetime,
        leadtime: timedelta,
        config: Optional[Union[dict, str, YAMLConfig, Path]] = None,
        dry_run: bool = False,
        key_path: Optional[list[str]] = None,
        batch: bool = False,
        schema_file: Optional[Path] = None,
        controller: Optional[str] = None,
    ):
        super().__init__(
            cycle=cycle,
            leadtime=leadtime,
            config=config,
            dry_run=dry_run,
            key_path=key_path,
            batch=batch,
            schema_file=schema_file,
            controller=controller,
        )
        self._cycle = cycle
        self._leadtime = leadtime

    @property
    def cycle(self):
        """
        The cycle.
        """
        return self._cycle

    @property
    def leadtime(self):
        """
        The leadtime.
        """
        return self._leadtime


class DriverTimeInvariant(Driver):
    """
    An abstract class for standalone time-invariant component drivers.
    """

    def __init__(
        self,
        config: Optional[Union[dict, str, YAMLConfig, Path]] = None,
        dry_run: bool = False,
        key_path: Optional[list[str]] = None,
        batch: bool = False,
        schema_file: Optional[Path] = None,
        controller: Optional[str] = None,
    ):
        super().__init__(
            config=config,
            dry_run=dry_run,
            key_path=key_path,
            batch=batch,
            schema_file=schema_file,
            controller=controller,
        )


DriverT = Union[type[Assets], type[Driver]]


def _add_docstring(class_: type, omit: Optional[list[str]] = None) -> None:
    """
    Dynamically add docstring to a driver class.

    :param class_: The class to add the docstring to.
    :param omit: Parameters to omit from the docstring.
    """
    base = """
    A driver.

    :param cycle: The cycle.
    :param leadtime: The leadtime.
    :param config: Path to config file (read stdin if missing or None).
    :param dry_run: Run in dry-run mode?
    :param key_path: Keys leading through the config to the driver's configuration block.
    :param batch: Run component via the batch system?
    :param schema_file: Path to schema file to use to validate an external driver.
    :param controller: Name of block in config controlling run-time values.
    """
    setattr(
        class_,
        "__doc__",
        "\n".join(
            line
            for line in dedent(base).strip().split("\n")
            if not any(line.startswith(f":param {o}:") for o in omit or [])
        ),
    )


_add_docstring(Assets, omit=[STR.batch])
_add_docstring(AssetsCycleBased, omit=[STR.batch, STR.leadtime])
_add_docstring(AssetsCycleLeadtimeBased, omit=[STR.batch])
_add_docstring(AssetsTimeInvariant, omit=[STR.batch, STR.cycle, STR.leadtime])
_add_docstring(Driver)
_add_docstring(DriverCycleBased, omit=[STR.leadtime])
_add_docstring(DriverCycleLeadtimeBased)
_add_docstring(DriverTimeInvariant, omit=[STR.cycle, STR.leadtime])
