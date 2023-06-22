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
from importlib import import_module

from uwtools.utils import file_helpers
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

    def load_config(self, config_file):
        '''
        Load the configuration file.

        '''
        modname = "uwtools.apps.UW" if len(sys.argv) > 1 else "uwtools.apps.SRW210"
        load_config = getattr(import_module(modname), "load_config")
        self.load_config(config_file)

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
