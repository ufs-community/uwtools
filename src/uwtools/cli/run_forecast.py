# pylint: disable=duplicate-code
"""
CLI for running a forecast.
"""

import sys
from argparse import ArgumentParser, HelpFormatter, Namespace
from typing import List

from uwtools.drivers import forecast
from uwtools.utils import cli_helpers


def main() -> None:
    """
    Defines the user interface for the forecast driver.

    Parses arguments provided by the user and passes to the Forecast driver class to be run.
    """
    args = parse_args(sys.argv[1:])
    name = "run-forecast"
    cli_helpers.setup_logging(
        log_file=args.log_file, log_name=name, quiet=args.quiet, verbose=args.verbose
    )
    forecast_class = getattr(forecast, "%sForecast" % args.forecast_model)
    experiment = forecast_class(args.config_file, args.machine, log_name=name)
    experiment.run()


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
        type=cli_helpers.path_if_file_exists,
    )
    optional.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Validate configuration but do not run the forecast.",
    )
    optional.add_argument(
        "-l",
        "--log-file",
        default="/dev/null",
        help="Path to a specified log file",
        metavar="FILE",
    )
    optional.add_argument(
        "-m",
        "--machine",
        help="Path to YAML platform-definition file",
        metavar="FILE",
        type=cli_helpers.path_if_file_exists,
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
    optional.add_argument(
        "--forecast-app",
        choices={"HAFS", "MRW", "SRW"},
        help="The app to be run",
    )
    optional.add_argument(
        "--forecast-model",
        choices={"CCPP", "CICE", "CMEPS", "FV3", "MOM6"},
        help="The experiment to be run",
    )
    parsed = parser.parse_args(args)
    if parsed.quiet and parsed.verbose:
        print("Options --dry-run and --outfile may not be used together", file=sys.stderr)
        sys.exit(1)
    return parsed
