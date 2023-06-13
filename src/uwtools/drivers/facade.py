#!/usr/bin/env python3
#pylint: disable=unused-import, unused-variable, unused-argument
# remove these disables once implemented
'''
This file contains the scaffolding for the strangler pattern wrapper. 
It is a python script that will be called by the user to run the 
manage experiments. It will call the other tools in the uwtools package 
to do the work. It will also be responsible for setting up the 
working directory and moving files around. 

See UW documentation for more information:
https://github.com/ufs-community/workflow-tools/wiki/Implementation-of-a-Service-Oriented-Architecture-Fa%C3%A7ade
'''

import abc

class Facade: # pragma: no cover
    #remove pragma when completed

    ''' 
    This base class provides the interface to methods used to read in
    a user-provided YAML configuration file, validate it, create the
    necessary experiment directory and manager files, then link the 
    fix files as needed.

    Attributes
    ----------
    config_path : Path
        The file path to the configuration file to be parsed.

    Methods
    -------
    load_config()
        Load the configuration file.
    
    validate_config()
        Validate the configuration file.
    
    create_experiment()
        Create the experiment directory.
    
    create_manager_files()
        Create the manager files.
    
    link_fix_files()
        Link the fix files.
    '''

    def __init__(self, argv):

        '''
        Initialize the facade driver.

        '''

    @abc.abstractmethod
    def load_config(self, config_file):
        '''
        Load the configuration file. This is the concrete implementation of the strangler pattern. This will 
        at first call the old code, but will eventually call the new code. 

        '''

    @abc.abstractmethod
    def validate_config(self):
        '''
        Validate the configuration file.

        '''

    @abc.abstractmethod
    def create_experiment(self):
        '''
        Create the experiment directory.

        '''

    @abc.abstractmethod
    def create_manager_files(self):
        '''
        Create the manager files.

        '''

    @abc.abstractmethod
    def link_fix_files(self):
        '''
        Link the fix files.

        '''
