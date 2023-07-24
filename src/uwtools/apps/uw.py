"""
This file contains the specific drivers for a particular app, using the facade pattern base class.
"""

from importlib import resources

from uwtools import config, config_validator
from uwtools.drivers.facade import Facade
from uwtools.logger import Logger


class UWforSRW(Facade):
    """
    Concrete class to handle UFS Short Range Weather app forecasts.
    """

    def __init__(self):
        """
        Initialize the facade driver.
        """
        with resources.as_file(resources.files("uwtools.resources")) as path:
            self.schema = (path / "workflow.jsonschema").as_posix()

    def load_config(self, config_file: str) -> None:
        """
        Load the configuration file.
        """
        config_obj = config.YAMLConfig(config_file)
        config_obj.dump_file("config.yaml")

    def validate_config(self, config_file: str) -> bool:
        """
        Validate the configuration file.

        This will use the config_validator module to validate the config file. The current version
        parses config.yaml, but later versions can individually check that each created j-job has a
        valid config.
        """
        return config_validator.config_is_valid(
            config_file=config_file,
            validation_schema=self.schema,
            log=Logger(),
        )

    def create_experiment(self) -> None:
        """
        Create the experiment directory.
        """

    def create_manager_files(self) -> None:
        """
        Create the manager files.
        """

    def link_fix_files(self) -> None:
        """
        Link the fix files.
        """
