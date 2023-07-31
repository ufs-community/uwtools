"""
This file contains the specific drivers for a particular app, using the facade pattern base class.
"""

from importlib import resources

from uwtools import config
from uwtools.drivers import driver
from uwtools.drivers.facade import Facade


class UWforSRW(Facade):
    """
    Concrete class to handle UFS Short Range Weather app forecasts.
    """

    def __init__(self):
        """
        Initialize the facade driver.
        """

    def load_config(self, config_file: str) -> None:  # pragma: no cover
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
        with resources.as_file(resources.files("uwtools.resources")) as path:
            schema = (path / "workflow.jsonschema").as_posix()

        method = driver.Driver.validate
        return method(config_file=config_file, schema=schema)

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
