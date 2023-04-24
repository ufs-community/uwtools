#!/usr/bin/env python3
#pylint: disable=unused-import, unused-variable, unused-argument
# remove these disables once implemented
'''
This file contains the scaffolding for the forecast driver. 
It is a python script that will be called by the user to run the 
forecast. It will call the other tools in the uwtools package 
to do the work. It will also be responsible for setting up the 
working directory and moving files around. 

See UW documentation for more information:
https://github.com/ufs-community/workflow-tools/wiki/Migrating-Production-Workflows-to-the-Unified-Workflow-using-the-Strangler-Fig-Pattern#component-drivers
'''

import abc
import argparse
import inspect
import os

from uwtools.utils import cli_helpers

def parse_args(argv):

    '''
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documentation for more information about settings
     of each argument.
    '''
    parser = argparse.ArgumentParser(
       description='Set config with user-defined settings.'
    )
    parser.add_argument(
        '-c', '--config_file',
        help='path to YAML configuration file',
        type=cli_helpers.path_if_file_exists,
    )
    parser.add_argument(
        '-m', '--machine',
        help='path to YAML platform definition file',
        type=cli_helpers.path_if_file_exists,
    )
    parser.add_argument(
        '-d', '--dry_run',
        action='store_true',
        help='If provided, validate configuration but do not run the forecast',
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='If provided, print all logging messages.',
        )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='If provided, print no logging messages',
        )
    parser.add_argument(
        '-l', '--log_file',
        help='Optional path to a specified log file',
        default=os.path.join(os.path.dirname(__file__), "forecast.log")
        )
    return parser.parse_args(argv)

class Forecast:

    ''' 
    This base class provides the interface to methods used to read in
    a user-provided YAML configuration file, convert it to the required
    config file, fix files, and namelist for a forecast. Subsequent
    methods will be used to stage the input files and run the forecast.        
    
    Attributes
    ----------
    config_path : Path
        The file path to the configuration file to be parsed.

    Methods
    -------
    requirements()  
        Recursively parse config and platform files to determine and
        fill in any dependencies.

    resources()
        Determine necessary task objects and fill in resource requirements of each.
        Returns a Config object containing the HPC resources needed.

    validate()
        Validates the objects generated by the driver from the provided
        config and platform files. If the --dry_run flag is provided, complete all
        stages through validation and print results without running the forecast.

    main()
        Main method for the driver. Calls the other methods in the driver           
        to run the forecast.

    create_model_config()
        Collects all the user inputs required to create a model config
        file, calling the existing model config tools. 

    stage_fix_files()   
        Holds the knowledge for how to modify a list of fix files and
        stages them in the working directory.

    create_namelist()
        Collects all the user inputs required to create a namelist
        file, calling the existing namelist config tools.

    stage_output_files()
        Holds the knowledge for how to modify a list of output files and
        stages them in the working directory.

    job_card()
        Turns the resources config object into a batch card for the 
        configured Task. Can be called from the command line on the front end 
        node to show the user what the job card would have looked like.

    run()
        Runs the forecast executable with the namelist file and staged
        input files. This will both build the executable and run it.
    
    '''

    def __init__(self, argv):

        '''
        Initialize the Forecast driver.

        '''
        self.args = parse_args(argv)

    def requirements(self):

        ''' Recursively parse config and platform files to determine and
         fill in any dependencies. '''

    def resources(self):

        ''' Determine necessary task objects and fill in resource requirements of each.
         Returns a Config object containing the HPC resources needed.'''

    def validate(self):

        ''' Validates the objects generated by the driver from the provided
        config and platform files. If the --dry_run flag is provided, complete all
        stages through validation and print results without running the forecast.'''

    def main(self, argv):
        '''
        Defines the user interface for the forecast driver. Parses arguments provided by the user
        and passes to the Forecast driver class to be run.'''
        self.args = parse_args(argv)

    @abc.abstractmethod
    def create_model_config(self):

        ''' Collects all the user inputs required to create a model config 
        file, calling the existing model config tools. This will be unique
        to the app being run and will appropriately parse subsequent stages
        of the workflow. 
        Defaults will be filled in if not provided by the user. Equivalent 
        references to config_default.yaml or config.community.yaml from SRW
        will need to be made for the other apps. '''

    @abc.abstractmethod
    def stage_fix_files(self):

        ''' Holds the knowledge for how to modify a list of fix files and 
        stages them in the working directory. Likely gets all its info from 
        config_obj. Calls data mover tool (could be python copy). Fix files 
        usually are specific to a given named grid and resolution. '''

    @abc.abstractmethod
    def create_namelist(self):

        ''' Collects all the user inputs required to create a namelist 
        file, calling the existing namelist config tools. '''

    @abc.abstractmethod
    def stage_output_files(self):

        ''' Holds the knowledge for how to modify a list of output files and 
        stages them in the working directory. Output files usually are 
        specific to a given app.'''

    @abc.abstractmethod
    def job_card(self):

        ''' Turns the resources config object into a batch card for the 
        configured Task. Can be called from the command line on the front end 
        node to show the user what the job card would have looked like.'''

    @abc.abstractmethod
    def run(self):

        ''' Runs the forecast executable with the namelist file and staged
        input files. This will both build the executable and run it. '''

class SRWForecast:

    '''
        Concrete class to handle UFS Short Range Weather app forecasts.
    '''

    def __init__(self, argv):
        '''
            Initialize the Forecast driver.

        '''
        super().__init__(argv)

    def main(self, argv):
        '''
        Defines the user interface for the forecast driver. Parses arguments provided by the user
        and passes to the Forecast driver class to be run.'''
        user_args = parse_args(argv)

        # Set up logging
        name = f"{inspect.stack()[0][3]}"
        log = cli_helpers.setup_logging(user_args, log_name=name)

        forecast = Forecast(user_args)
        forecast.run()

    def create_model_config(self):
        ''' Create SRW model config file. '''

    def stage_fix_files(self):
        ''' Create list of SRW fix files and stage them in the working 
        directory. '''

    def create_namelist(self):
        ''' Collects all the user inputs required to create a namelist 
        file, calling the existing namelist config tools. For SRW,
        this will take the fix files and model_config previously created to
        to generate config.yaml'''

    def stage_output_files(self):
        ''' Create list of SRW output files and stage them in the working 
        directory.'''

    def job_card(self):
        ''' Turns the resources config object into a batch card for the 
        configured Task.'''

    def run(self):
        ''' Runs the forecast executable with the namelist file and staged
        input files. This will both build the executable and run it. '''
