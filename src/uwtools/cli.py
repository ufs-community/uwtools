"""
Modal CLI support.
"""

import sys
from argparse import ArgumentParser as Parser
from argparse import HelpFormatter, Namespace
from argparse import _ArgumentGroup as Group
from argparse import _SubParsersAction as Subparsers
from typing import List

# Arguments

# pylint: disable=missing-function-docstring


def add_arg_dry_run(group: Group) -> None:
    group.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="print rendered template only",
    )


def add_arg_input_template(group: Group, required: bool = False) -> None:
    group.add_argument(
        "--input-template",
        "-i",
        help="path to an atparse template file",
        metavar="FILE",
        required=required,
        type=str,
    )


def add_arg_outfile(group: Group, required: bool) -> None:
    group.add_argument(
        "--outfile",
        "-o",
        help="path to new Jinja2 template",
        metavar="FILE",
        required=required,
        type=str,
    )


def add_arg_quiet(group: Group) -> None:
    group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="print no logging messages",
    )


def add_arg_verbose(group: Group) -> None:
    group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="print all logging messages",
    )


# Main modes


def add_subparser_config(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "config", help="work with config files", formatter_class=formatter
    )
    subparsers = parser.add_subparsers(metavar="<mode>", required=True)
    add_subparser_config_render(subparsers)
    add_subparser_config_translate(subparsers)
    add_subparser_config_validate(subparsers)
    return parser


def add_subparser_experiment(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "experiment", help="configure and run experiments", formatter_class=formatter
    )
    subparsers = parser.add_subparsers(metavar="<mode>", required=True)
    add_subparser_experiment_configure(subparsers)
    add_subparser_experiment_run(subparsers)
    add_subparser_experiment_validate(subparsers)


def add_subparser_forecast(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(
        "forecast", help="configure and run forecasts", formatter_class=formatter
    )
    subparsers = parser.add_subparsers(metavar="<mode>", required=True)
    add_subparser_forecast_configure(subparsers)
    add_subparser_forecast_restart(subparsers)
    add_subparser_forecast_run(subparsers)
    add_subparser_forecast_validate(subparsers)


# Submodes of config


def add_subparser_config_render(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser("render", help="render config files")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_config_translate(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser("translate", help="translate config files")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_config_validate(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser("config", help="validate config files")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


# Submodes of experiment


def add_subparser_experiment_configure(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser("configure", help="configure an experiment")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_experiment_run(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser("run", help="run an experiment")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_experiment_validate(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser("validate", help="validate an experiment")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


# Submodes of forecast


def add_subparser_forecast_configure(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser("configure", help="configure an forecast")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_forecast_restart(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser("restart", help="restart an forecast")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_forecast_run(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser("run", help="run an forecast")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_forecast_validate(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser("validate", help="validate an forecast")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


# pylint: enable=missing-function-docstring


# General


def abort(msg: str) -> None:
    """
    Exit with an informative message and error status.

    :param msg: The message to print.
    """
    print(msg, file=sys.stderr)
    sys.exit(1)


def check_args(parsed_args: Namespace) -> Namespace:
    """
    Validate basic correctness of CLI arguments.
    """
    try:
        if not parsed_args.dry_run and not parsed_args.outfile:
            abort("Specify either --dry-run or --outfile")
    except AttributeError:
        pass
    return parsed_args


def formatter(prog: str) -> HelpFormatter:
    """
    A standard formatter for help messages.
    """
    return HelpFormatter(prog, max_help_position=8)


def main() -> None:
    """
    Main entry point.
    """
    args = check_args(parse_args(sys.argv[1:]))
    print(args)
    # dispatch to appropriate handler...


def parse_args(cli_args: List[str]) -> Namespace:
    """
    Parse CLI arguments.

    Please see Python's argparse documentation for more information about settings of each argument.
    """

    parser = Parser(description="Unified Workflow Tools", formatter_class=formatter)
    subparsers = parser.add_subparsers(metavar="<mode>", required=True)
    add_subparser_config(subparsers)
    add_subparser_experiment(subparsers)
    add_subparser_forecast(subparsers)
    return parser.parse_args(cli_args)
