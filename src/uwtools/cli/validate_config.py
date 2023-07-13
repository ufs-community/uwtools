# pylint: disable=duplicate-code
"""
CLI for JSON Schema-based config validation.
"""
import argparse
import sys
from argparse import HelpFormatter, Namespace
from typing import List

from uwtools.config_validator import config_is_valid
from uwtools.utils import cli_helpers


def main() -> None:
    """
    Main entry point.
    """
    args = parse_args(sys.argv[1:])
    name = "validate-config"
    log = cli_helpers.setup_logging(
        log_file=args.log_file, log_name=name, quiet=args.quiet, verbose=args.verbose
    )
    valid = config_is_valid(
        config_file=args.config_file, validation_schema=args.validation_schema, log=log
    )
    sys.exit(0 if valid else 1)


def parse_args(args: List[str]) -> Namespace:
    """
    Parse CLI arguments.
    """
    args = args or ["--help"]
    parser = argparse.ArgumentParser(
        description="Validate a YAML config with JSON Schema.",
        formatter_class=lambda prog: HelpFormatter(prog, max_help_position=8),
    )
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "-c",
        "--config-file",
        help="Path to bash/ini, namelist, or YAML configuration file",
        metavar="FILE",
        required=True,
        type=cli_helpers.path_if_file_exists,
    )
    required.add_argument(
        "-s",
        "--validation-schema",
        help="Path to JSON Schema file for validation",
        metavar="FILE",
        required=True,
        type=cli_helpers.path_if_file_exists,
    )
    optional = parser.add_argument_group("optional arguments")
    optional.add_argument(
        "--config-file-type",
        help="Convert config file to this type.",
        choices={"F90", "INI", "YAML"},
    )
    optional.add_argument(
        "-l",
        "--log-file",
        default="/dev/null",
        help="Log to this file.",
        metavar="FILE",
    )
    optional.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Print no log messages.",
    )
    optional.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print all log messages.",
    )
    parsed = parser.parse_args(args)
    if parsed.quiet and parsed.verbose:
        print("Options --dry-run and --outfile may not be used together", file=sys.stderr)
        sys.exit(1)
    return parsed
