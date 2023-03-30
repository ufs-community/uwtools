#!/usr/bin/env python3
#pylint: disable=too-many-branches, too-many-statements, too-many-locals

'''
This utility creates a command line interface for handling config files.
'''
import os
import sys
import argparse
import pathlib
from uwtools import config
from uwtools.logger import Logger



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
        '--show_format',
        action='store_true',
        help='If provided, print the required formatting to generate the requested output file',
    )

    parser.add_argument(
        '--values_needed',
        action='store_true',
        help='If provided, prints a list of required configuration settings to stdout',
    )

    parser.add_argument(
        '--input_file_type',
        help='If provided, will convert provided input file to provided file type.\
            Accepts YAML, bash/ini or namelist',
    )

    parser.add_argument(
        '--config_file_type',
        help='If provided, will convert provided config file to provided file type.\
            Accepts YAML, bash/ini or namelist',
    )

    parser.add_argument(
        '--output_file_type',
        help='If provided, will convert provided output file to provided file type.\
            Accepts YAML, bash/ini or namelist',
    )
    return parser.parse_args(argv)

def create_config_obj(argv):
    '''Main section for processing config file'''

    logfile = os.path.join(os.path.dirname(__file__), "set_config.log")
    log = Logger(level='info',
        _format='%(message)s',
        colored_log= False,
        logfile_path=logfile
        )

    user_args = parse_args(argv)

    infile_type = user_args.input_file_type or get_file_type(user_args.input_base_file)

    if infile_type in [".yaml", ".yml"]:
        config_obj = config.YAMLConfig(user_args.input_base_file)
        infile_type = ".yaml"

    elif infile_type in [".bash", ".sh", ".ini", ".IN"]:
        config_obj = config.INIConfig(user_args.input_base_file)
        infile_type = ".ini"

    elif infile_type == ".nml":
        config_obj = config.F90Config(user_args.input_base_file)

    else:
        log.critical("Set config failure: bad file type")
        raise ValueError("Set config failure: input base file not compatible")


    if user_args.config_file:
        config_file_type = user_args.config_file_type or get_file_type(user_args.config_file)

        if config_file_type in [".yaml", ".yml"]:
            user_config_obj = config.YAMLConfig(user_args.config_file)
            config_file_type = ".yaml"

        elif config_file_type in [".bash", ".sh", ".ini", ".IN"]:
            user_config_obj = config.INIConfig(user_args.config_file)
            config_file_type = ".ini"

        elif config_file_type == ".nml":
            user_config_obj = config.F90Config(user_args.config_file)

        if config_file_type != infile_type:
            config_depth = user_config_obj.dictionary_depth(user_config_obj.data)
            input_depth = config_obj.dictionary_depth(config_obj.data)

            if input_depth < config_depth:
                log.critical(f"{user_args.config_file} not compatible with input file")
                raise ValueError("Set config failure: config object not compatible with input file")

        config_obj.update_values(user_config_obj)

    if user_args.values_needed:
        set_var = []
        jinja2_var = []
        empty_var = []
        config_obj.iterate_values(config_obj.data, set_var, jinja2_var, empty_var, parent="")
        log.info('Keys that are complete:')
        for var in set_var:
            log.info(var)
        log.info('')
        log.info('Keys that have unfilled jinja2 templates:')
        for var in jinja2_var:
            log.info(var)
        log.info('')
        log.info('Keys that are set to empty:')
        for var in empty_var:
            log.info(var)
        return

    if user_args.dry_run:
        if user_args.outfile:
            out_object = user_args.outfile
            log.info(f'warning file {out_object} ',
                 r"not written when using --dry_run")
        # apply switch to allow user to view the results of config
        # instead of writing to disk
        log.info(config_obj)
        return

    if user_args.outfile:
        outfile_type = user_args.output_file_type or get_file_type(user_args.outfile)
        if outfile_type != infile_type:
            if outfile_type in [".yaml", ".yml"]:
                out_object = config.YAMLConfig()
            elif outfile_type in [".bash", ".sh", ".ini", ".IN"]:
                if config_obj.dictionary_depth(config_obj.data) > 2:
                    log.critical("Set config failure: incompatible file types")
                    raise ValueError("Set config failure: output object not compatible with input")
                out_object = config.INIConfig()
            elif outfile_type == ".nml":
                if config_obj.dictionary_depth(config_obj.data) != 2:
                    log.critical("Set config failure: incompatible file types")
                    raise ValueError("Set config failure: output object not compatible with input")
                out_object = config.F90Config()
            else:
                out_object = config.FieldTableConfig()

            out_object.update(config_obj)

            output_depth = out_object.dictionary_depth(out_object.data)
            input_depth = config_obj.dictionary_depth(config_obj.data)

            if input_depth > output_depth:
                log.critical(f"{user_args.outfile} not compatible with {user_args.input_base_file}")
                raise ValueError("Set config failure: output object not compatible with input file")

        else: # same type of file as input, no need to convert it
            out_object = config_obj
        out_object.dump_file(user_args.outfile)


    # if --show_format, print a list of required configuration settings to stdout
    if user_args.show_format:
        if user_args.outfile is None:
        # first ensure all required args are present
            raise argparse.ArgumentError(user_args.outfile, \
                "args: --show_format also requires -outfile for reference")

        if outfile_type != infile_type:
            log.info(help(out_object.dump_file))

if __name__ == '__main__':
    create_config_obj(sys.argv[1:])
