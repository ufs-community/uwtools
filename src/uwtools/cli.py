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


# pylint: enable=missing-function-docstring

# Subcommands


def add_subparser_config(subparsers: Subparsers) -> None:
    """
    Add a 'config' mode subparser.
    """
    parser = subparsers.add_parser("config", help="manipulate configuration files")
    # required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_experiment(subparsers: Subparsers) -> None:
    """
    Add a 'experiment' mode subparser.
    """
    parser = subparsers.add_parser("experiment", help="configure and run experiments")
    # required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_forecast(subparsers: Subparsers) -> None:
    """
    Add a 'forecast' mode subparser.
    """
    parser = subparsers.add_parser("forecast", help="configure and run forecasts")
    # required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


# General


def abort(msg: str) -> None:
    """
    Exit with an informative message and error status.
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

    cli_args = cli_args or ["--help"]
    parser = Parser(
        description="Unified Workflow Tools",
        formatter_class=lambda prog: HelpFormatter(prog, max_help_position=8),
    )
    subparsers = parser.add_subparsers(metavar="mode")
    add_subparser_config(subparsers)
    add_subparser_experiment(subparsers)
    add_subparser_forecast(subparsers)
    return parser.parse_args(cli_args)
