"""
This file contains the concrete facades for a variety of apps.
"""

import sys
from importlib import import_module

from uwtools.drivers.facade import Facade


class SRWExperiment(Facade):
    """
    Concrete class to handle UFS Short Range Weather app forecasts.
    """

    def __init__(self):
        """
        Initialize the facade driver.
        """
        self.modname = (
            "uwtools.apps.uw.UWforSRW" if len(sys.argv) > 1 else "uwtools.apps.srw.SRW210"
        )
        # Note: for alternate versions, manually set the modname to the appropriate app version
        # see the src/uwtools/apps/ directory for options

    def load_config(self, config_file):  # pragma: no cover
        # NB: Remove pragma: no cover ASAP
        """
        Load the configuration file.
        """

        import_config_file = getattr(import_module(self.modname), "load_config")  # pragma: no cover
        import_config_file(config_file)

    def validate_config(self, config_file):
        """
        Validate the configuration file.
        """

    def create_experiment(self):  # pragma: no cover
        # NB: Remove pragma: no cover ASAP
        """
        Create the experiment directory.
        """
        # Note: UW version coming soon, replace module with self.modname when available
        workflow_generator = getattr(import_module("uwtools.apps.srw.SRW210"), "create_experiment")
        workflow_generator()

    def create_manager_files(self):
        """
        Create the manager files.
        """

    def link_fix_files(self):
        """
        Link the fix files.
        """
