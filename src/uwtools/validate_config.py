"""
Validate a config using JSON Schema.
"""
import json
import logging
import os
import sys

import jsonschema

from uwtools import config, exceptions
from uwtools.utils import cli_helpers
from uwtools.logger import Logger
from uwtools.config import YAMLConfig

def validate_config(config_file: str, validation_schema: str, log: Logger) -> None:

    # Get the config file to be validated and dereference Jinja2 templates.
    # The config file will only be 2 levels deep.

    config_obj = YAMLConfig(config_file, log_name=log.name)
    config_obj.dereference_all()

    # Load the JSON Schema validation schema.

    with open(validation_schema, "r", encoding="utf-8") as schema_file:
        schema = json.load(schema_file)

    # Validate the config file against the schema file.

    schema_error = 0
    validator = jsonschema.Draft7Validator(schema)

    # Print out each schema error.

    errors = validator.iter_errors(config_obj.data)
    for error in errors:
        schema_error += 1
        logging.error(error)
        logging.error("------")

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
                    logging.error("%s has Invalid Path %s", value, config_obj.data[field][value])

    if schema_error > 0:
        sys.exit(f"This configuration file has {schema_error} errors")
    else:
        sys.exit(0)


if __name__ == "__main__":
    cli_args = parse_args(sys.argv[1:])
    LOG_NAME = "validate_config"
    cli_log = cli_helpers.setup_logging(cli_args, log_name=LOG_NAME)
    try:
        validate_config(sys.argv[1:], cli_log)
    except exceptions.UWConfigError as e:
        sys.exit(e)
