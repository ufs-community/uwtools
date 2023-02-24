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

def get_file_type(arg):
    '''Gets the file type from the path'''
    return pathlib.Path(arg).suffix

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
        help='Path to a config base file. Accepts YAML, bash/ini or namelist',
        required=True,
        type=path_if_file_exists,
    )

    parser.add_argument(
        '-o', '--outfile',
        help='Full path to output file. If different from input, will will perform conversion.\
            For field table output, specify model such as "field_table.FV3_GFS_v16"',
    )

    parser.add_argument(
        '--out_file_type',
        help='Optional output file type override',
    )

    parser.add_argument(
        '-c', '--config_file',
        help='Optional path to configuration file. Accepts YAML, bash/ini or namelist',
        type=path_if_file_exists,
    )

    parser.add_argument(
        '-d', '--dry_run',
        action='store_true',
        help='If provided, print rendered config file to stdout only',
    )

    parser.add_argument(
        '--values_needed',
        action='store_true',
        help='If provided, print a list of required configuration settings to stdout',
    )
    return parser.parse_args(argv)


def create_config_obj(argv):
    '''Main section for processing config file'''

    user_args = parse_args(argv)
    infile_type = get_file_type(user_args.input_base_file)

    if infile_type in [".yaml", ".yml"]:
        config_obj = config.YAMLConfig(user_args.input_base_file)
        infile_type = ".yaml"

    elif infile_type in [".bash", ".sh", ".ini", ".IN"]:
        config_obj = config.INIConfig(user_args.input_base_file)
        infile_type = ".ini"

    elif infile_type == ".nml":
        config_obj = config.F90Config(user_args.input_base_file)

    else:
        print("Set config failure: bad file type")


    if user_args.config_file:
        config_file_type = get_file_type(user_args.config_file)

        if config_file_type in [".yaml", ".yml"]:
            user_config_obj = config.YAMLConfig(user_args.config_file)
            config_file_type = ".yaml"

        elif config_file_type in [".bash", ".sh", ".ini", ".IN"]:
            user_config_obj = config.INIConfig(user_args.config_file)
            config_file_type = ".ini"

        elif config_file_type == ".nml":
            user_config_obj = config.F90Config(user_args.config_file)

        config_obj.update_values(user_config_obj)

    if user_args.outfile:
        outfile_type = get_file_type(user_args.outfile)
        if outfile_type != infile_type:
            if outfile_type in [".yaml", ".yml"] and infile_type != ".yaml":
                out_object = config.YAMLConfig()
                out_object.update(config_obj.data)
                outfile_type = ".yaml"
            elif outfile_type in [".bash", ".sh", ".ini", ".IN"] and infile_type != ".ini":
                out_object = config.INIConfig()
                out_object.update(config_obj.data)
                outfile_type = ".ini"
            elif outfile_type == ".nml":
                out_object = config.F90Config()
                out_object.update(config_obj.data)
            else:
                out_object = config.FieldTableConfig()
                out_object.update(config_obj)
        else:
            out_object = config_obj
        out_object.dump_file(user_args.outfile)

if __name__ == '__main__':
    create_config_obj(sys.argv[1:])
