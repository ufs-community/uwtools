"""
Modal CLI support.
"""

import sys
from argparse import ArgumentParser as Parser
from argparse import HelpFormatter, Namespace
from argparse import _ArgumentGroup as Group
from typing import List

from uwtools.utils import atparse_to_jinja2, cli_helpers

# Argument parsing.


# description="Convert an atparse template to Jinja2.",

# pylint: disable=missing-function-docstring


def add_arg_dry_run(parser: Group) -> None:
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Print rendered template to stdout only.",
    )


def add_arg_input_template(parser: Group) -> None:
    parser.add_argument(
        "-i",
        "--input-template",
        help="Path to an atparse template file",
        metavar="FILE",
        required=True,
        type=cli_helpers.path_if_it_exists,
    )


def add_arg_outfile(parser: Group) -> None:
    parser.add_argument(
        "-o",
        "--outfile",
        help="Path to new Jinja2 template",
        metavar="FILE",
    )


def add_arg_quiet(parser: Group) -> None:
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Print no logging messages.",
    )


def add_arg_verbose(parser: Group) -> None:
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print all logging messages.",
    )


# pylint: enable=missing-function-docstring


def check_args(parsed_args: Namespace) -> Namespace:
    """
    Validate basic correctness of CLI arguments.
    """
    if not parsed_args.dry_run and not parsed_args.outfile:
        print("Specify either --dry-run or --outfile", file=sys.stderr)
        sys.exit(1)
    return parsed_args


def get_args(cli_args: List[str]) -> Namespace:
    """
    Return parsed and checked CLI arguments.
    """
    return check_args(parse_args(cli_args))


def main() -> None:
    """
    Main entry point.
    """
    args = get_args(sys.argv[1:])
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

    # Arguments applicable to all sub-commands:

    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)

    # required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")
    return parser.parse_args(cli_args)


# Entry point functions.


def main_atparse_to_jinja2() -> None:
    """
    Entry point for 'uw config translate'.
    """
    args = parse_args(sys.argv[1:])
    atparse_to_jinja2.convert(
        input_template=args.input_template, outfile=args.outfile, dry_run=args.dry_run
    )
