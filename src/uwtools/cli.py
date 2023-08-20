"""
Modal CLI.
"""

import sys
from argparse import ArgumentParser as Parser
from argparse import HelpFormatter, Namespace
from argparse import _ArgumentGroup as Group
from argparse import _SubParsersAction as Subparsers
from typing import List

# Main logic


def check_args(parsed_args: Namespace) -> Namespace:
    """
    Validate basic argument correctness.

    :param parsed_args: The parsed command-line arguments to check.
    :return: The checked command-line arguments.
    :raises: SystemExit if any checks failed.
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


def parse_args(cli_args: List[str]) -> Namespace:
    """
    Parse command-line arguments.

    :param cli_args: The raw command-line arguments to parse.
    :return: Parsed command-line arguments.
    """

    parser = Parser(description="Unified Workflow Tools", formatter_class=formatter)
    subparsers = parser.add_subparsers(metavar="MODE", required=True)
    add_subparser_config(subparsers)
    add_subparser_experiment(subparsers)
    add_subparser_forecast(subparsers)
    return parser.parse_args(cli_args)


# Support


def abort(msg: str) -> None:
    """
    Exit with an informative message and error status.

    :param msg: The message to print.
    """
    print(msg, file=sys.stderr)
    sys.exit(1)


def formatter(prog: str) -> HelpFormatter:
    """
    A standard formatter for help messages.
    """
    return HelpFormatter(prog, max_help_position=8)


# Mode: config


def add_subparser_config(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'config'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = subparsers.add_parser(
        "config", help="work with config files", formatter_class=formatter
    )
    subparsers = parser.add_subparsers(metavar="MODE", required=True)
    add_subparser_config_render(subparsers)
    add_subparser_config_translate(subparsers)
    add_subparser_config_validate(subparsers)


def add_subparser_config_render(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'config render'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = subparsers.add_parser("render", help="render config files", formatter_class=formatter)
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_config_translate(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'config translate'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = subparsers.add_parser(
        "translate", help="translate config files", formatter_class=formatter
    )
    required = parser.add_argument_group("required arguments")
    add_arg_input_format(required)
    add_arg_output_format(required)
    optional = parser.add_argument_group("optional arguments")
    add_arg_input_file(optional)
    add_arg_output_file(optional)
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_config_validate(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'config validate'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = subparsers.add_parser(
        "config", help="validate config files", formatter_class=formatter
    )
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


# Mode: experiment


def add_subparser_experiment(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'experiment'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = subparsers.add_parser(
        "experiment", help="configure and run experiments", formatter_class=formatter
    )
    subparsers = parser.add_subparsers(metavar="MODE", required=True)
    add_subparser_experiment_configure(subparsers)
    add_subparser_experiment_run(subparsers)
    add_subparser_experiment_validate(subparsers)


def add_subparser_experiment_configure(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'experiment configure'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = subparsers.add_parser(
        "configure", help="configure an experiment", formatter_class=formatter
    )
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_experiment_run(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'experiment run'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = subparsers.add_parser("run", help="run an experiment")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_experiment_validate(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'experiment validate'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = subparsers.add_parser(
        "validate", help="validate an experiment", formatter_class=formatter
    )
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


# Mode: forecast


def add_subparser_forecast(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'forecast'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = subparsers.add_parser(
        "forecast", help="configure and run forecasts", formatter_class=formatter
    )
    subparsers = parser.add_subparsers(metavar="MODE", required=True)
    add_subparser_forecast_configure(subparsers)
    add_subparser_forecast_run(subparsers)
    add_subparser_forecast_validate(subparsers)


def add_subparser_forecast_configure(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'forecast configure'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = subparsers.add_parser(
        "configure", help="configure an forecast", formatter_class=formatter
    )
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_forecast_run(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'forecast run'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = subparsers.add_parser("run", help="run an forecast")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_forecast_validate(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'forecast validate'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = subparsers.add_parser(
        "validate", help="validate an forecast", formatter_class=formatter
    )
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


# Arguments

# pylint: disable=missing-function-docstring


# def add_arg_dry_run(group: Group) -> None:
#     group.add_argument(
#         "--dry-run",
#         action="store_true",
#         help="print rendered template only",
#     )


def add_arg_input_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        "--input-file",
        "-i",
        help="path to input file",
        metavar="PATH",
        required=required,
        type=str,
    )


def add_arg_input_format(group: Group) -> None:
    group.add_argument(
        "--input-format",
        choices=["atparse"],
        help="input-data format",
        metavar="FORMAT",
        required=True,
        type=str,
    )


# def add_arg_input_template(group: Group, required: bool = False) -> None:
#     group.add_argument(
#         "--input-template",
#         "-i",
#         help="path to an atparse template file",
#         metavar="FILE",
#         required=required,
#         type=str,
#     )


# def add_arg_outfile(group: Group, required: bool) -> None:
#     group.add_argument(
#         "--outfile",
#         "-o",
#         help="path to new Jinja2 template",
#         metavar="FILE",
#         required=required,
#         type=str,
#     )


def add_arg_output_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        "--output-file",
        "-o",
        help="path to output file",
        metavar="PATH",
        required=required,
        type=str,
    )


def add_arg_output_format(group: Group) -> None:
    group.add_argument(
        "--output-format",
        choices=["ini", "nml", "yaml"],
        help="output-data format",
        metavar="FORMAT",
        required=True,
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
