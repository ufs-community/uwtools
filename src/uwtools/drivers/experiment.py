"""
This file contains the concrete facades for a variety of apps.
"""

import sys

from uwtools.apps.srw import SRW210
from uwtools.apps.uw import UWforSRW
from uwtools.drivers.facade import Facade

# from importlib import import_module


class SRWExperiment(Facade):
    """
    Concrete class to handle UFS Short Range Weather app forecasts.
    """

    def __init__(self):
        """
        Initialize the facade driver.
        """

        # Note: for alternate versions, manually set self.srwobj to the appropriate app version
        # see the src/uwtools/apps/ directory for options
        # The following steps parse the modname to call later funtions appropriately
        self.srwobj = UWforSRW() if len(sys.argv) > 1 else SRW210()

    def load_config(self, config_file: str) -> None:  # pragma: no cover
        # NB: Remove pragma: no cover ASAP
        """
        Load the configuration file.
        """
        self.srwobj.load_config(config_file)

    def validate_config(self, config_file: str) -> bool:
        """
        Validate the configuration file.
        """
        return self.srwobj.validate_config(config_file)

    def create_experiment(self):  # pragma: no cover
        # NB: Remove pragma: no cover ASAP
        """
        Create the experiment directory.
        """
        # Note: UW version coming soon, replace module with self.srwobj when available
        srwobj = SRW210()
        srwobj.create_experiment()

    def create_manager_files(self):
        """
        Create the manager files.
        """

    def link_fix_files(self):
        """
        Link the fix files.
        """
