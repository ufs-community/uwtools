"""
Provides an abstract class representing drivers for various NWP tools.
"""

from abc import ABC, abstractmethod
from typing import Optional

from uwtools import config_validator
from uwtools.logger import Logger


class Driver(ABC):
    """
    An abstract class representing drivers for various NWP tools.
    """

    def __init__(self, config_file: str, log: Optional[Logger] = None):
        """
        Initialize the driver.
        """
        self.log = log if log is not None else Logger()
        self._config_file = config_file
        self._validate()

    # Public methods

    @abstractmethod
    def batch_script(self) -> None:
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
    def resources(self) -> None:
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
    def schema(self) -> str:
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
            validation_schema=self.schema,
            log=self.log,
        )
