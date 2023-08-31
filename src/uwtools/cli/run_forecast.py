# pylint: disable=duplicate-code
"""
CLI for running a forecast.
"""

import sys
from argparse import ArgumentParser, HelpFormatter, Namespace
from typing import List

from uwtools.drivers import forecast
from uwtools.exceptions import UWConfigError
from uwtools.logging import setup_logging
from uwtools.utils import cli_helpers


def main() -> None:
    """
    Defines the user interface for the forecast driver.

    Parses arguments provided by the user and passes to the Forecast driver class to be run.
    """
    args = parse_args(sys.argv[1:])
    setup_logging(quiet=args.quiet, verbose=args.verbose)

    forecast_class = getattr(forecast, f"{args.forecast_model}Forecast")
    forecast_obj = forecast_class(
        config_file=args.config_file,
        dry_run=args.dry_run,
        batch_script=args.batch_script,
    )
    try:
        forecast_obj.run()
    except UWConfigError as e:
        sys.exit(str(e))


def parse_args(args: List[str]) -> Namespace:
    """
    Function maintains the arguments accepted by this script.

    Please see Python's argparse documentation for more information about settings of each argument.
    """
    args = args or ["--help"]
    parser = ArgumentParser(
        description="Set config with user-defined settings.",
        formatter_class=lambda prog: HelpFormatter(prog, max_help_position=8),
    )
    optional = parser.add_argument_group("optional arguments")
    optional.add_argument(
        "-c",
        "--config-file",
        help="Path to YAML configuration file",
        metavar="FILE",
        type=cli_helpers.path_if_it_exists,
    )
    optional.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Validate configuration but do not run the forecast.",
    )
    optional.add_argument(
        "--forecast-model",
        choices={"FV3"},
        help="The experiment to be run",
    )
    optional.add_argument(
        "--batch_script",
        help=(
            "Optional name for a batch script to be generated and run. "
            "Default is to run the mpi command directly. "
        ),
        metavar="FILE",
    )
    optional.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Print no logging messages.",
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
