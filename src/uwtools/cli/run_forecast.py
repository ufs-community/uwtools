# pylint: disable=unused-import, unused-variable, unused-argument
# remove these disables once implemented
"""
This utility creates a command line interface for running a forecast.
"""

import argparse
import inspect
import os
import sys

from uwtools.drivers import forecast
from uwtools.utils import cli_helpers


def parse_args(argv):  # pragma: no cover
    # remove pragma when completed

    """
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documentation for more information about settings
     of each argument.
    """
    parser = argparse.ArgumentParser(description="Set config with user-defined settings.")
    parser.add_argument(
        "-c",
        "--config_file",
        help="path to YAML configuration file",
        type=cli_helpers.path_if_file_exists,
    )
    parser.add_argument(
        "-m",
        "--machine",
        help="path to YAML platform definition file",
        type=cli_helpers.path_if_file_exists,
    )
    parser.add_argument(
        "--forecast_app",
        help="If provided, will define the app to be run.\
            Currently accepts SRW, MRW, or HAFS",
        choices=["SRW", "MRW", "HAFS"],
    )
    parser.add_argument(
        "--forecast_model",
        nargs="+",
        help="If provided, will define the experiment to be run.\
            Currently accepts FV3, CCPP, MOM6, CICE, and/or CMEPS",
        choices=["FV3", "CCPP", "MOM6", "CICE", "CMEPS"],
    )
    parser.add_argument(
        "-d",
        "--dry_run",
        action="store_true",
        help="If provided, validate configuration but do not run the forecast",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="If provided, print all logging messages.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="If provided, print no logging messages",
    )
    parser.add_argument(
        "-l",
        "--log_file",
        help="Optional path to a specified log file",
        default=os.path.join(os.path.dirname(__file__), "forecast.log"),
    )
    return parser.parse_args(argv)


def main(argv):  # pragma: no cover
    """
    Defines the user interface for the forecast driver. Parses arguments
    provided by the user and passes to the Forecast driver class to be run."""
    user_args = parse_args(argv)

    # Set up logging
    name = f"{inspect.stack()[0][3]}"
    log = cli_helpers.setup_logging(user_args, log_name=name)

    forecast_type = user_args.forecast_model.join()
    forecast_class = getattr(forecast, f"{forecast_type}Forecast")
    experiment = forecast_class(user_args.config_file, user_args.machine, log_name=name)

    experiment.run()
