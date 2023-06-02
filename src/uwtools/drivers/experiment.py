#!/usr/bin/env python3
#pylint: disable=unused-import, unused-variable, unused-argument, useless-parent-delegation
# remove these disables once implemented
'''
This file contains the concrete facades for a variety of apps.
'''

import logging
import os
import sys

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

    def load_config(self):
        '''
        Load the configuration file and validate it.

        '''

    def validate_config(self):
        '''
        Validate the configuration file.

        '''

    def create_experiment(self):
        '''
        Create the experiment directory and manager files.

        '''

    def create_directory_structure(self, run_directory, exist_act="delete"):
        ''' Collects the name of the desired run directory, and has an
        optional flag for what to do if the run directory specified already
        exists. Creates the run directory and adds subdirectories
        INPUT and RESTART. Verifies creation of all directories.

        Args:
           run_directory: path of desired run directory
           exist_act: - could be any of 'delete', 'rename', 'quit'
                      - how program should act if run directory exists
                      - default is to delete old run directory
           Returns: None
        '''

        # Caller should only provide correct argument
        if exist_act not in ["delete", "rename", "quit"]:
            raise ValueError("Bad argument to create_directory_structure")

        # Exit program with error if caller chooses to quit
        if exist_act == "quit" and os.path.isdir(run_directory):
            logging.critical("User chose quit option when creating directory")
            sys.exit(1)

        # Delete or rename directory if it exists
        file_helpers.handle_existing(run_directory, exist_act)

        # Create new run directory with two required subdirectories
        try:
            for subdir in ("INPUT", "RESTART"):
                # Create and verify new directory with subdirectories
                os.makedirs(os.path.join(run_directory, subdir))
                if not os.path.isdir(os.path.join(run_directory, subdir)):
                    msg = f"Directory {run_directory} with {subdir} not created"
                    logging.critical(msg)
                    raise RuntimeError(msg)
            msg = f"Directory {run_directory} created with subdirectories"
            logging.info(msg)
        except (RuntimeError, FileExistsError) as create_error:
            msg = f"Could not create directory {run_directory} with subdirectories"
            raise RuntimeError(msg) from create_error

    def create_manager_files(self):
        '''
        Create the manager files.

        '''

    def link_fix_files(self):
        '''
        Link the fix files.

        '''
