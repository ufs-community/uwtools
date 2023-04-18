#!/usr/bin/env python3
#pylint: disable=unused-import, unused-variable, unused-argument
'''
This file contains the scaffolding for the forecast driver. 
It is a python script that will be called by the user to run the 
forecast. It will call the other tools in the uwtools package 
to do the work. It will also be responsible for setting up the 
working directory and moving files around.
'''

import argparse
import inspect
import logging
import os
import sys

from uwtools.j2template import J2Template
from uwtools import config

def parse_args(argv):

    '''
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documentation for more information about settings
     of each argument.
    '''

def create_model_config():

    ''' Collects all the user inputs required to create a model config 
    file, calling the existing model config tools. This will be unique
    to the app being run and will appropriately parse subsequent stages
    of the workflow. 
    Defaults will be filled in if not provided by the user. Equivalent 
    references to config_default.yaml or config.community.yaml from SRW
    will need to be made for the other apps. '''

def stage_fix_files():

    ''' Holds the knowledge for how to modify a list of fix files and 
    stages them in the working directory. Likely gets all its info from 
    config_obj. Calls data mover tool (could be python copy). Fix files 
    usually are specific to a given named grid and resolution. '''

def create_namelist():

    ''' Collects all the user inputs required to create a namelist 
    file, calling the existing namelist config tools. For SRW,
    this will take the fix files and model_config previously created to
    generate config.yaml'''

def stage_output_files():

    ''' Holds the knowledge for how to modify a list of output files and 
    stages them in the working directory. Output files usually are 
    specific to a given app.'''

def run_forecast():

    ''' Runs the forecast executable with the namelist file and staged
    input files. This will both build the executable and run it. '''
