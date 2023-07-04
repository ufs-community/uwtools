"""
This utility creates a command line interface for running a forecast.
"""

import inspect
import sys
from argparse import ArgumentParser, HelpFormatter

from uwtools.drivers import forecast
from uwtools.utils import cli_helpers


def parse_args(args):
    """
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documentation for more information about settings
    of each argument.
    """
    args = args or ["--help"]
    parser = ArgumentParser(
        description="Set config with user-defined settings.",
        formatter_class=lambda prog: HelpFormatter(prog, max_help_position=8),
    )
    # required = parser.add_argument_group("required arguments")
    # #PM# ARE THERE REALLY NO REQUIRED ARGUMENTS?
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
        # #PM# WHAT TO DO ABOUT THIS LOGFILE PATH?
        default="/dev/null",  # os.path.join(os.path.dirname(__file__), "forecast.log"),
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
        choices=["SRW", "MRW", "HAFS"],
        help="The app to be run",
    )
    optional.add_argument(
        "--forecast-model",
        choices=["FV3", "CCPP", "MOM6", "CICE", "CMEPS"],
        help="The experiment to be run",
        nargs="+",
    )
    return parser.parse_args(args)


def main():
    """
    Defines the user interface for the forecast driver. Parses arguments
    provided by the user and passes to the Forecast driver class to be run."""
    user_args = parse_args(sys.argv[1:])
    name = f"{inspect.stack()[0][3]}"
    cli_helpers.setup_logging(
        log_file=user_args.log_file, log_name=name, quiet=user_args.quiet, verbose=user_args.verbose
    )
    forecast_type = user_args.forecast_model.join()
    forecast_class = getattr(forecast, f"{forecast_type}Forecast")
    experiment = forecast_class(user_args.config_file, user_args.machine, log_name=name)
    experiment.run()
