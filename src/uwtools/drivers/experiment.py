#!/usr/bin/env python3
#pylint: disable=unused-import, unused-variable, unused-argument, useless-parent-delegation
# remove these disables once implemented
'''
This file contains the concrete facades for a variety of apps.
'''

import logging
import os
import sys
import shutil
import subprocess

from uwtools.utils import file_helpers
from uwtools.utils import cli_helpers
from uwtools import config
from .facade import Facade

logging.getLogger(__name__)


class SRWExperiment(Facade): # pragma: no cover
    #remove pragma when completed

    '''
        Concrete class to handle UFS Short Range Weather app forecasts.
    '''
    def __init__(self, argv):

        '''
        Initialize the facade driver.

        '''
        super().__init__(argv)

    def _old_config(self, config_file):
        '''
        Load the configuration file.

        '''
        file_type = cli_helpers.get_file_type(config_file)
        if file_type == 'INI':
            with open('config.yaml', 'w', encoding="utf-8") as file_name:
                ## Note: this is a temporary path until parsing the SRW directory is implemented
                subprocess.call(["python", "config_utils.py", "-c", config_file, "-t",
                             "$PWD/config_defaults.yaml", "-o", "yaml"], stdout=file_name)
        elif file_type == 'YAML':
            shutil.copy2(config_file, 'config.yaml')
        else:
            msg = f"Bad file type -- {file_type}. Cannot load configuration!"
            logging.critical(msg)
            raise ValueError(msg)

    def _new_config(self, config_file):

        '''
        Load the configuration file.

        '''
        config_obj = config.YAMLConfig(config_file)
        config_obj.dump_file('config.yaml')

    def load_config(self, config_file):
        '''
        Load the configuration file.

        '''
        switch = "old"
        if switch == "old":
            self._old_config(config_file)
        elif switch == "new":
            self._new_config(config_file)

    def validate_config(self):
        '''
        Validate the configuration file.

        '''

    def create_experiment(self):
        '''
        Create the experiment directory.

        '''

    def create_manager_files(self):
        '''
        Create the manager files.

        '''

    def link_fix_files(self):
        '''
        Link the fix files.

        '''
