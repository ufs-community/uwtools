#!/usr/bin/env python3
#pylint: disable=unused-import, unused-variable, unused-argument
# remove these disables once implemented
'''
This utility creates a command line interface for managing an experiment.
'''

import argparse
import inspect
import os
import sys

from uwtools.drivers import experiment
from uwtools.utils import cli_helpers


def parse_args(argv):# pragma: no cover
    #remove pragma when completed

    '''
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documentation for more information about settings
     of each argument.
    '''
    parser = argparse.ArgumentParser(
       description='Set config with user-defined settings.'
    )
    parser.add_argument(
        '--forecast_app',
        help='If provided, will define the app to be run.\
            Currently accepts SRW, MRW, or HAFS',
        choices=["SRW", "MRW", "HAFS"],
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


def manager(argv): # pragma: no cover
    '''
    Defines the user interface for the experiment manager. Parses arguments
    provided by the user and passes to the facade to be run.'''
    user_args = parse_args(argv)

    # Set up logging
    name = f"{inspect.stack()[0][3]}"
    log = cli_helpers.setup_logging(user_args, log_name=name)

    experiment_class = getattr(experiment, f"{user_args.forecast_app}Experiment")
    managed_experiment = experiment_class(user_args.config_file, log_name=name)

    managed_experiment.load_config()


if __name__ == '__main__':
    manager(sys.argv[1:])
