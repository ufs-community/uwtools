"""
This file contains the specific drivers for a particular app, using the facade pattern base class.
"""

from uwtools import config
from uwtools.drivers.facade import Facade


class UWforSRW(Facade):
    """
    Concrete class to handle UFS Short Range Weather app forecasts.
    """

    def __init__(self):
        """
        Initialize the facade driver.

        """

    def load_config(self, config_file):
        """
        Load the configuration file.

        """
        config_obj = config.YAMLConfig(config_file)
        config_obj.dump_file("config.yaml")

    def validate_config(self, config_file):
        """
        Validate the configuration file.

        """

    def create_experiment(self):
        """
        Create the experiment directory.

        """

    def create_manager_files(self):
        """
        Create the manager files.

        """

    def link_fix_files(self):
        """
        Link the fix files.

        """
