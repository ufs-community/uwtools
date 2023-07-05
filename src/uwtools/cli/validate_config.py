"""
CLI for JSON Schema-based config validation
"""
import inspect
import argparse
# import inspect
# import json
# import logging
import os
import sys
from typing import List
from argparse import Namespace
# import jsonschema

# from uwtools import config, exceptions
from uwtools.utils import cli_helpers
from uwtools.config_validator import validate_config

def main() -> None:
    args = parse_args(sys.argv[1:])
    name = f"{inspect.stack()[0][3]}"
    log = cli_helpers.setup_logging(
        log_file=args.log_file, log_name=name, quiet=args.quiet, verbose=args.verbose
    )


def parse_args(args: List[str]) -> Namespace:
    """
    Parse CLI arguments.
    """
    parser = argparse.ArgumentParser(description="Validate config with user-defined settings.")
    group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        "-s",
        "--validation_schema",
        help="Path to a validation schema.",
        required=True,
        type=cli_helpers.path_if_file_exists,
    )
    parser.add_argument(
        "-c",
        "--config_file",
        help="Path to configuration file. Accepts YAML, bash/ini or namelist",
        required=True,
        type=cli_helpers.path_if_file_exists,
    )
    parser.add_argument(
        "--config_file_type",
        help="If used, will convert provided config file to given file type.\
            Accepts YAML, bash/ini or namelist",
        choices=["YAML", "INI", "F90"],
    )
    group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="If provided, print all logging messages.",
    )
    group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="If provided, print no logging messages",
    )
    parser.add_argument(
        "-l",
        "--log_file",
        help="Optional path to a specified log file",
        default=os.path.join(os.path.dirname(__file__), "set_config.log"),
    )
    return parser.parse_args(args)
