#!/usr/bin/env python3
#pylint: disable=unused-import, unused-variable, unused-argument, useless-parent-delegation
# remove these disables once implemented
'''
This file contains the specific drivers for a particular app, using the facade pattern base class.
'''

import logging
import os
import sys
import shutil
import subprocess

from uwtools.utils import file_helpers
from uwtools.utils import cli_helpers
from ..drivers.facade import Facade

class SRW210(Facade): # pragma: no cover
    #remove pragma when completed

    '''
        Concrete class to handle UFS Short Range Weather app forecasts.
        Methods call manual command line processes as described in the docs.
        UFS Short Range Weather app, release v2.1.0
    '''
    def __init__(self, argv):

        '''
        Initialize the facade driver.

        '''
        super().__init__(argv)

    def load_config(self, config_file):
        '''
        Load the configuration file.

        '''
        file_type = cli_helpers.get_file_type(config_file)
        if file_type == 'INI':
            with open('config.yaml', 'w', encoding="utf-8") as file:
                ## Note: this is a temporary path until parsing the SRW directory is implemented
                subprocess.run(f"python config_utils.py -c {config_file} -t $PWD/config_defaults.yaml -o yaml"
                               , capture_output=True, check=False, shell=True, stdout=file)
        elif file_type == 'YAML':
            shutil.copy2(config_file, 'config.yaml')
        else:
            msg = f"Bad file type -- {file_type}. Cannot load configuration!"
            logging.critical(msg)
            raise ValueError(msg)

    def validate_config(self, config_file):
        '''
        Validate the configuration file.

        '''

    def create_experiment(self):
        '''
        Generate the regional workflow.
        This sets up the workflow based on config.yaml, links fix files, creates input.nml and FV3LAM_wflow.xml.
        '''
        # Note: this is a temporary path until parsing the SRW directory is implemented
        subprocess.run("python generate_FV3LAM_wflow.py", check=False, shell=True)

    def create_manager_files(self):
        '''
        Create the manager files.

        '''

    def link_fix_files(self):
        '''
        Link the fix files.

        '''
