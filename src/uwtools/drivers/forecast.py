#!/usr/bin/env python3
#pylint: disable=unused-import, unused-variable, unused-argument, useless-parent-delegation
# remove these disables once implemented
'''
This file contains the forecast drivers for a variety of apps
and physics suites.
'''

import logging
import os
import sys
from datetime import datetime
import shutil

from .driver import Driver

logging.getLogger(__name__)


class FV3Forecast(Driver): # pragma: no cover
    #remove pragma when completed

    '''
        Concrete class to handle UFS Short Range Weather app forecasts.
        FV3 (ATM-only) mode.
    '''

    def __init__(self, argv):
        '''
            Initialize the Forecast driver.

        '''
        super().__init__(argv)

    def requirements(self):

        ''' Recursively parse config and platform files to determine and
         fill in any dependencies. '''

    def resources(self):

        ''' Determine necessary task objects and fill in resource
            requirements of each.
         Returns a Config object containing the HPC resources needed.'''

    def validate(self):

        ''' Validates the objects generated by the driver from the provided
        config and platform files.'''

    def create_model_config(self):

        ''' Collects all the user inputs required to create a model config
        file, calling the existing model config tools. This will be unique
        to the app being run and will appropriately parse subsequent stages
        of the workflow.
        Defaults will be filled in if not provided by the user. Equivalent
        references to config_default.yaml or config.community.yaml from SRW
        will need to be made for the other apps. '''

    def stage_fix_files(self):

        ''' Holds the knowledge for how to modify a list of fix files and
        stages them in the working directory. Likely gets all its info from
        config_obj. Calls data mover tool (could be python copy). Fix files
        usually are specific to a given named grid and resolution. '''

    def create_namelist(self):
        ''' Collects all the user inputs required to create a namelist
        file, calling the existing namelist config tools. For SRW,
        this will take the fix files and model_config previously created to
        to generate config.yaml'''

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

        # Caller can only provide correct argument
        if exist_act not in ["delete", "rename", "quit"]:
            raise ValueError("Bad argument to create_directory_structure")

        # Exit program with error if caller chooses to quit
        if exist_act == "quit":
            logging.critical("User chose quit option")
            sys.exit(1)

        # Try to delete existing run directory if option is delete
        try:
            if exist_act == "delete" and os.path.isdir(run_directory):
                shutil.rmtree(run_directory)
        except (RuntimeError, FileExistsError) as del_error:
            raise RuntimeError("Could not delete " +
                               "old run directory") from del_error

        # Try to rename existing run directory if caller chooses rename
        try:
            if exist_act == "rename" and os.path.isdir(run_directory):
                now = datetime.now()
                save_dir = run_directory + now.strftime("_%Y%m%d_%H%M%S")
                shutil.move(run_directory, save_dir)
        except (RuntimeError, FileExistsError) as rename_error:
            raise RuntimeError("Could not rename " +
                               "old run directory") from rename_error

        # Create new run directory with two required subdirectories
        try:
            os.makedirs(os.path.join(run_directory, "INPUT"))
            os.makedirs(os.path.join(run_directory, "RESTART"))
            # Verify creation of new directory with subdirectories
            if not os.path.isdir(os.path.join(run_directory, "RESTART")):
                logging.critical("New run directories not created")
                sys.exit(1)
            logging.info("New run directories created")
        except (RuntimeError, FileExistsError) as create_error:
            raise RuntimeError("Could not create " +
                               "new run directories") from create_error

    def output(self):
        ''' Create list of SRW output files and stage them in the working
        directory.'''

    def job_card(self):
        ''' Turns the resources config object into a batch card for the
        configured Task.'''

    def run(self):
        ''' Runs the forecast executable with the namelist file and staged
        input files. This will both build the executable and run it. '''
