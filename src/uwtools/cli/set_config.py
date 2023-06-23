#pylint: disable=too-many-branches, too-many-statements, too-many-locals

'''
This utility creates a command line interface for handling config files.
'''
import argparse
import inspect
import os
import sys

from uwtools import config
from uwtools import exceptions
from uwtools.utils import cli_helpers


def parse_args(argv):

    '''
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documentation for more information about settings of each
    argument.
    '''

    parser = argparse.ArgumentParser(
       description='Set config with user-defined settings.'
    )

    group = parser.add_mutually_exclusive_group()

    parser.add_argument(
        '-i', '--input_base_file',
        help='Path to a config base file. Accepts YAML, bash/ini or namelist',
        required=True,
        type=cli_helpers.path_if_file_exists,
    )

    parser.add_argument(
        '-o', '--outfile',
        help='Full path to output file. If different from input, will will perform conversion.\
            For field table output, specify model such as "field_table.FV3_GFS_v16"',
    )

    parser.add_argument(
        '-c', '--config_file',
        help='Optional path to configuration file. Accepts YAML, bash/ini or namelist',
        type=cli_helpers.path_if_file_exists,
    )

    parser.add_argument(
        '-d', '--dry_run',
        action='store_true',
        help='If provided, print rendered config file to stdout only',
    )

    parser.add_argument(
        '--compare',
        action='store_true',
        help='If provided, show diff between -i and -c files.',
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
        choices=["YAML", "INI", "F90"],
    )

    parser.add_argument(
        '--config_file_type',
        help='If provided, will convert provided config file to provided file type.\
            Accepts YAML, bash/ini or namelist',
        choices=["YAML", "INI", "F90"],
    )

    parser.add_argument(
        '--output_file_type',
        help='If provided, will convert provided output file to provided file type.\
            Accepts YAML, bash/ini or namelist',
        choices=["YAML", "INI", "F90", "FieldTable"],
    )
    group.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='If provided, print all logging messages.',
        )
    group.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='If provided, print no logging messages',
        )
    parser.add_argument(
        '-l', '--log_file',
        help='Optional path to a specified log file',
        default=os.path.join(os.path.dirname(__file__), "set_config.log")
        )

    args = parser.parse_args(argv)
    if args.quiet and args.dry_run:
        msg = "You added quiet and dry_run arguments. This will print nothing."
        raise argparse.ArgumentError(None, msg)

    return parser.parse_args(argv)

def create_config_obj(argv, log=None):
    '''Main section for processing config file'''

    user_args = parse_args(argv)

    if log is None:
        name = f"{inspect.stack()[0][3]}"
        log = cli_helpers.setup_logging(user_args, log_name=name)

    infile_type = user_args.input_file_type or cli_helpers.get_file_type(user_args.input_base_file)

    config_class = getattr(config, f"{infile_type}Config")
    config_obj = config_class(user_args.input_base_file, log_name=log.name)

    if user_args.config_file:
        config_file_type = user_args.config_file_type or \
                cli_helpers.get_file_type(user_args.config_file)

        user_config_obj = getattr(config,
                         f"{config_file_type}Config")(user_args.config_file)

        if config_file_type != infile_type:
            config_depth = user_config_obj.dictionary_depth(user_config_obj.data)
            input_depth = config_obj.dictionary_depth(config_obj.data)

            if input_depth < config_depth:
                log.critical(f"{user_args.config_file} not compatible with input file")
                raise ValueError("Set config failure: config object not compatible with input file")

        if user_args.compare:
            log.info(f"- {user_args.input_base_file}")
            log.info(f"+ {user_args.config_file}")
            log.info("-"*80)
            config_obj.compare_config(user_config_obj)
            return

        config_obj.update_values(user_config_obj)

    config_obj.dereference_all()

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
            log.info(f'warning file {user_args.outfile} ',
                 r"not written when using --dry_run")
        # apply switch to allow user to view the results of config
        # instead of writing to disk
        log.info(config_obj)
        return

    if user_args.outfile:
        outfile_type = user_args.output_file_type or cli_helpers.get_file_type(user_args.outfile)

        if outfile_type != infile_type:

            out_object = getattr(config, f"{outfile_type}Config")()
            out_object.update(config_obj)

            output_depth = out_object.dictionary_depth(out_object.data)
            input_depth = config_obj.dictionary_depth(config_obj.data)

            # Check for incompatible conversion objects

            err_msg = "Set config failure: incompatible file types"
            if (outfile_type == "INI" and input_depth > 2) or \
                    (outfile_type == "F90" and input_depth != 2):
                log.critical(err_msg)
                raise ValueError(err_msg)

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

def main():
    cli_args = parse_args(sys.argv[1:])
    LOG_NAME = "set_config"
    cli_log = cli_helpers.setup_logging(cli_args, log_name=LOG_NAME)
    try:
        create_config_obj(sys.argv[1:], cli_log)
    except exceptions.UWConfigError as e:
        sys.exit(e)
