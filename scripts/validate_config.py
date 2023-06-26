#!/usr/bin/env python3
#pylint: disable=too-many-branches, too-many-statements, too-many-locals

'''
This utility validates a config file using a validation schema.
'''
import argparse
import inspect
import logging
import os
import sys
import json
import jsonschema

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
       description='Validate config with user-defined settings.'
    )

    group = parser.add_mutually_exclusive_group()

    parser.add_argument(
        '-s', '--validation_schema',
        help='Path to a validation schema.',
        required=True,
        type=cli_helpers.path_if_file_exists,
    )

    parser.add_argument(
        '-c', '--config_file',
        help='Path to configuration file. Accepts YAML, bash/ini or namelist',
        required=True,
        type=cli_helpers.path_if_file_exists,
    )

    parser.add_argument(
        '--config_file_type',
        help='If used, will convert provided config file to given file type.\
            Accepts YAML, bash/ini or namelist',
        choices=["YAML", "INI", "F90"],
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

    return parser.parse_args(argv)


def validate_config(argv, log=None):
    '''Main section for validating config file'''

    user_args = parse_args(argv)

    if log is None:
        name = f"{inspect.stack()[0][3]}"
        log = cli_helpers.setup_logging(user_args, log_name=name)

    # Get the config file to be validated and dereference jinja templates
    # The config file will only be 2 levels deep
    config_class = getattr(config, "YAMLConfig")
    config_obj = config_class(user_args.config_file, log_name=log.name)
    config_obj.dereference_all()

    # Load the json validation schema
    # This json file is created using the jsonschema syntax
    with open(user_args.validation_schema, 'r',
              encoding="utf-8") as schema_file:
        schema = json.load(schema_file)

    schema_error = 0

    # Validate the config file against the schema file
    validator = jsonschema.Draft7Validator(schema)

    # Print out each schema error
    errors = validator.iter_errors(config_obj.data)

    for error in errors:
        schema_error += 1
        logging.error(error)
        logging.error('------')

    # Create a list of fields that could contain a file or path
    path_list = []
    for field in schema["properties"]:
        for value in schema["properties"][field]["properties"]:
            # the json pair "format": "uri" labels a path or file
            if "format" in schema["properties"][field]["properties"][value]:
                path_list.append(value)

    # Check for existence of those files or paths
    for field in config_obj.data:
        for value in config_obj.data[field]:
            if value in path_list:
                if not os.path.exists(config_obj.data[field][value]):
                    schema_error += 1
                    logging.error('%s has Invalid Path %s',
                                  value, config_obj.data[field][value])

    if schema_error > 0:
        sys.exit(f'This configuration file has {schema_error} errors')
    else:
        sys.exit(0)


if __name__ == '__main__':

    cli_args = parse_args(sys.argv[1:])
    LOG_NAME = "validate_config"
    cli_log = cli_helpers.setup_logging(cli_args, log_name=LOG_NAME)
    try:
        validate_config(sys.argv[1:], cli_log)
    except exceptions.UWConfigError as e:
        sys.exit(e)
