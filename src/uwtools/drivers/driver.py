"""
Provides an abstract class representing drivers for various NWP tools.
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Optional

from uwtools.scheduler import BatchScript

from uwtools import config, config_validator


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

        self.config_data = config.YAMLConfig(self._config_file)

    # Public methods

    @abstractmethod
    def batch_script(self, platform_resources: Mapping) -> BatchScript:
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
    def resources(self, platform: dict) -> Mapping:
        """
        ???
        """

    @abstractmethod
    def run(self) -> None:
        """
        Run the NWP tool.
        """

    @abstractmethod
    def run_cmd(self, *args, run_cmd: str, exec_name: str) -> str:
        """
        The command-line command to run the NWP tool.
        """

    @property
    @abstractmethod
    def schema_file(self) -> str:
        """
        The path to the file containing the schema to validate the config file against.
        """

    # Private methods

    def _validate(self) -> bool:
        """
        Validate the user-supplied config file.
        """
        return config_validator.config_is_valid(
            config_file=self._config_file,
            schema_file=self.schema_file,
        )
