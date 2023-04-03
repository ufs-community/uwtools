"""

Helpers to be used when parsing arguments and gathering config files

"""

import argparse
import logging
import os
import pathlib
import sys

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

def setup_logging(user_args, logfile=None):

    ''' Create the Logger object '''

    log = Logger(level='info',
        _format='%(message)s',
        colored_log= False,
        logfile_path=logfile
        )
    if user_args.verbose:
        log.handlers.clear()
        log = Logger(level='debug',
            _format='%(asctime)s - %(levelname)-8s - %(name)-12s: %(message)s',
            colored_log= True,
            logfile_path=logfile
            )
        log.debug(r"Finished setting up debug file logging in {logfile}".format(logfile=logfile))
    elif user_args.quiet:
        log.handlers.clear()
        log.propagate = False

    return log

