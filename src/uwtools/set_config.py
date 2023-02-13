#!/usr/bin/env python3

'''
This utility creates a command line interface for handling config files.
'''
import os
import sys
import argparse
import pathlib
from uwtools import config



def path_if_file_exists(arg):
    '''Checks whether a file exists, and returns the path if it does.'''
    if not os.path.exists(arg):
        msg = f'{arg} does not exist!'
        raise argparse.ArgumentTypeError(msg)
    return arg

def get_file_type (arg):
    '''Gets the file type from the path'''
    return pathlib.Path(path_if_file_exists(arg)).suffix

def parse_args(argv):

    '''
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documentation for more information about settings of each
    argument.
    '''

    parser = argparse.ArgumentParser(
       description='Set config with user-defined settings.'
    )

    parser.add_argument(
        '-i', '--input_base_file',
        help='Path to a config base file.',
        required=True,
        type=path_if_file_exists,
        )

    parser.add_argument(
        '-o', '--outfile',
        help='Full path to output file',
        )

    parser.add_argument(
        '-c', '--config_file',
        help='Optional path to configuration file',
        type=path_if_file_exists,
    )

    parser.add_argument(
        '-d', '--dry_run',
        action='store_true',
        help='If provided, print rendered config file to stdout only',
    )
    return parser.parse_args(argv)


def create_config_obj (argv):
    '''Main section for processing config file'''

    user_args = parse_args(argv)
    file_type = get_file_type(user_args.input_base_file)

    if file_type in [".yaml", ".yml"]:
        config_obj = config.YAMLConfig(user_args.input_base_file)

    elif file_type in [".bash", ".sh", ".ini", ".IN"]:
        config_obj = config.INIConfig (user_args.input_base_file)

    elif file_type == ".nml":
        config_obj = config.F90Config (user_args.input_base_file)


    if user_args.config_file:
        config_file_type = get_file_type(user_args.config_file)

        if config_file_type in [".yaml", ".yml"]:
            user_config_obj = config.YAMLConfig(user_args.config_file)

        elif config_file_type in [".bash", ".sh", ".ini", ".IN"]:
            user_config_obj = config.INIConfig (user_args.config_file)

        elif config_file_type == ".nml":
            user_config_obj = config.F90Config (user_args.config_file)

        config_obj.update_values(user_config_obj)

    if user_args.outfile:
        config_obj.dump_file(user_args.outfile)

if __name__ == '__main__':
    create_config_obj(sys.argv[1:])
    