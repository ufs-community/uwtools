#!/usr/bin/env python3
# pylint: disable=unused-import, unused-variable, unused-argument, useless-parent-delegation
# remove these disables once implemented
"""
This file contains the specific drivers for a particular app, using the facade pattern base class.
"""

import logging
import os
import shutil
import subprocess
import sys

from uwtools import config
from uwtools.utils import cli_helpers, file_helpers

from ..drivers.facade import Facade


class UWforSRW(Facade):  # pragma: no cover
    # remove pragma when completed

    """
    Concrete class to handle UFS Short Range Weather app forecasts.
    """

    def __init__(self, argv):
        """
        Initialize the facade driver.

        """
        super().__init__(argv)

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
