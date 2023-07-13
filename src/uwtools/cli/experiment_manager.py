# pylint: disable=duplicate-code
"""
CLI for managing an experiment.
"""

import argparse
import sys
from argparse import HelpFormatter, Namespace
from typing import List

from uwtools.drivers import experiment
from uwtools.utils import cli_helpers


def main() -> None:
    """
    Defines the user interface for the experiment manager.

    Parses arguments provided by the user and passes to the facade to be run.
    """
    user_args = parse_args(sys.argv[1:])
    experiment_class = getattr(experiment, f"{user_args.forecast_app}Experiment")
    experiment_class(user_args.config_file)


def parse_args(args: List[str]) -> Namespace:
    """
    Function maintains the arguments accepted by this script.

    Please see Python's argparse documentation for more information about settings of each argument.
    """
    args = args or ["--help"]
    parser = argparse.ArgumentParser(
        description="Set config with user-defined settings.",
        formatter_class=lambda prog: HelpFormatter(prog, max_help_position=8),
    )
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "-a",
        "--forecast-app",
        choices={"SRW"},  # Will later include MRW, HAFS and more.
        help="Name of the app to run",
        metavar="APPNAME",
    )
    required.add_argument(
        "-c",
        "--config-file",
        help="Path to YAML, bash/ini, or namelist configuration file",
        metavar="FILE",
        type=cli_helpers.path_if_file_exists,
    )
    optional = parser.add_argument_group("optional arguments")
    optional.add_argument(
        "-l",
        "--log-file",
        default="/dev/null",
        help="Path to a file to log to",
        metavar="FILE",
    )
    optional.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Print no logging messages",
    )
    optional.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print all logging messages.",
    )
    parsed = parser.parse_args(args)
    if parsed.quiet and parsed.verbose:
        print("Options --dry-run and --outfile may not be used together", file=sys.stderr)
        sys.exit(1)
    return parsed
