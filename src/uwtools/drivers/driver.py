"""
An abstract class for component drivers.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from iotaa import asset, dryrun, external, tasks

from uwtools.config.formats.base import Config
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.validator import validate_internal
from uwtools.exceptions import UWConfigError, UWError
from uwtools.logging import log


class Driver(ABC):
    """
    An abstract class for component drivers.
    """

    def __init__(
        self,
        config: Optional[Union[dict, Path]],
        dry_run: bool = False,
        batch: bool = False,
        cycle: Optional[datetime] = None,
        key_path: Optional[List[str]] = None,
        leadtime: Optional[timedelta] = None,
    ) -> None:
        """
        A component driver.

        :param config: Path to config file (read stdin if missing or None).
        :param dry_run: Run in dry-run mode?
        :param batch: Run component via the batch system?
        :param cycle: The cycle.
        :param key_path: Keys leading through the config to the driver's configuration block.
        :param leadtime: The leadtime.
        """
        dryrun(enable=dry_run)
        self._config = YAMLConfig(config=config)
        self._batch = batch
        if leadtime and not cycle:
            raise UWError("When leadtime is specified, cycle is required")
        self._config.dereference(
            context={
                **({"cycle": cycle} if cycle else {}),
                **({"leadtime": leadtime} if leadtime else {}),
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
        }

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
        for schema_name in (self._driver_name.replace("_", "-"), "platform"):
            validate_internal(schema_name=schema_name, config=self._config)
