#pylint: disable=unused-variable
"""

Helpers to be used when parsing arguments and gathering config files

"""

import argparse
import logging
import os
import pathlib

from uwtools.logger import Logger


def dict_from_config_args(args):
    '''Given a list of command line arguments in the form key=value, return a
    dictionary of key/value pairs.'''
    return dict([arg.split('=') for arg in args])

def get_file_type(arg):
    ''' Returns a standardized file type given the suffix of the input
    arg. '''

    suffix = pathlib.Path(arg).suffix
    if suffix in [".yaml", ".yml"]:
        return "YAML"
    if suffix in [".bash", ".sh", ".ini", ".cfg"]:
        return "INI"
    if suffix in [".nml"]:
        return "F90"
    msg = f"Bad file suffix -- {suffix}. Cannot determine file type!"
    logging.critical(msg)
    raise ValueError(msg)

def path_if_file_exists(arg):
    ''' Checks whether a file exists, and returns the path if it does. '''
    if not os.path.exists(arg):
        msg = f'{arg} does not exist!'
        raise argparse.ArgumentTypeError(msg)

    return os.path.abspath(arg)

def setup_logging(user_args, log_name=None):

    ''' Create the Logger object '''

    args = {
        'level': 'info',
        '_format': '%(message)s',
        'colored_log': False,
        'logfile_path': user_args.log_file,
        'name': log_name,
        }

    if user_args.verbose:
        args['level'] = 'debug'
        args['colored_log'] = True
        del args['_format']

    log = Logger(**args)

    msg = f"Finished setting up debug file logging in {user_args.log_file}"
    log.debug(msg)

    if user_args.quiet:
        log.handlers.clear()
        log.propagate = False

    return log

def compare_files(expected, actual):
    '''Compare the content of two files.  Doing this over filecmp.cmp since 
    we may not be able to handle end-of-file character differences with it.
    Prints the contents of two compared files to std out if they do not match.'''

    with open(expected, 'r', encoding='utf-8') as expected_file:
        expected_content = expected_file.read().rstrip('\n')
    with open(actual, 'r', encoding='utf-8') as actual_file:
        actual_content = actual_file.read().rstrip('\n')

    if expected_content != actual_content:
        print('The expected file looks like:')
        print(expected_content)
        print('*' * 80)
        print('The rendered file looks like:')
        print(actual_content)
        return False
    return True
