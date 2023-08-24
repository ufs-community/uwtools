"""
Modal CLI.
"""

import sys
from argparse import ArgumentParser as Parser
from argparse import HelpFormatter, Namespace
from argparse import _ArgumentGroup as Group
from argparse import _SubParsersAction as Subparsers
from typing import List

import uwtools.config.atparse_to_jinja2
import uwtools.config.validator
from uwtools.logging import setup_logging

# Main logic


def check_args(args: Namespace) -> Namespace:
    """
    Validate basic argument correctness.

    :param args: The parsed command-line arguments to check.
    :return: The checked command-line arguments.
    :raises: SystemExit if any checks failed.
    """
    try:
        if args.quiet and args.verbose:
            abort("Specify at most one of --quiet, --verbose")
    except AttributeError:
        pass
    return args


def main() -> None:
    """
    Main entry point.
    """
    args = check_args(parse_args(sys.argv[1:]))
    setup_logging(quiet=args.quiet, verbose=args.verbose)
    modes = {
        "config": dispatch_config,
        "experiment": dispatch_experiment,
        "forecast": dispatch_forecast,
    }
    success = modes[args.mode](args)
    sys.exit(0 if success else 1)


def parse_args(raw_args: List[str]) -> Namespace:
    """
    Parse command-line arguments.

    :param raw_args: The raw command-line arguments to parse.
    :return: Parsed command-line arguments.
    """

    parser = Parser(description="Unified Workflow Tools", formatter_class=formatter)
    subparsers = parser.add_subparsers(dest="mode", metavar="MODE", required=True)
    add_subparser_config(subparsers)
    add_subparser_experiment(subparsers)
    add_subparser_forecast(subparsers)
    return parser.parse_args(raw_args)


# Support


def abort(msg: str) -> None:
    """
    Exit with an informative message and error status.

    :param msg: The message to print.
    """
    print(msg, file=sys.stderr)
    sys.exit(1)


def add_subparser(subparsers: Subparsers, name: str, msg: str) -> Parser:
    """
    Add a new subparser, with standard help formatting, to the given parser.

    :param subparsers: The subparsers to add the new subparser to.
    :param name: The name of the subparser.
    :param msg: The help message for the subparser.
    :return: The new subparser.
    """
    return subparsers.add_parser(name, help=msg, formatter_class=formatter)


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
    parser = add_subparser(subparsers, "config", "work with config files")
    subparsers = parser.add_subparsers(dest="submode", metavar="MODE", required=True)
    add_subparser_config_render(subparsers)
    add_subparser_config_translate(subparsers)
    add_subparser_config_validate(subparsers)


def add_subparser_config_render(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'config render'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "render", "render config files")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_config_translate(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'config translate'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "translate", "translate config files")
    required = parser.add_argument_group("required arguments")
    add_arg_input_format(required, choices=["atparse"])
    add_arg_output_format(required, choices=["jinja2"])
    optional = parser.add_argument_group("optional arguments")
    add_arg_input_file(optional)
    add_arg_output_file(optional)
    add_arg_dry_run(optional)
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_config_validate(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'config validate'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "validate", "validate config files")
    required = parser.add_argument_group("required arguments")
    add_arg_input_format(required, choices=["yaml"])
    add_arg_schema_file(required)
    optional = parser.add_argument_group("optional arguments")
    add_arg_input_file(optional)
    add_arg_quiet(optional)
    add_arg_verbose(optional)


# Mode: experiment


def add_subparser_experiment(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'experiment'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "experiment", "configure and run experiments")
    subparsers = parser.add_subparsers(dest="submode", metavar="MODE", required=True)
    add_subparser_experiment_configure(subparsers)
    add_subparser_experiment_run(subparsers)
    add_subparser_experiment_validate(subparsers)


def add_subparser_experiment_configure(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'experiment configure'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "configure", "configure an experiment")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_experiment_run(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'experiment run'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "run", "run an experiment")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_experiment_validate(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'experiment validate'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "validate", "validate an experiment")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


# Mode: forecast


def add_subparser_forecast(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'forecast'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "forecast", "configure and run forecasts")
    subparsers = parser.add_subparsers(metavar="MODE", required=True)
    add_subparser_forecast_configure(subparsers)
    add_subparser_forecast_run(subparsers)
    add_subparser_forecast_validate(subparsers)


def add_subparser_forecast_configure(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'forecast configure'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "configure", "configure an forecast")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_forecast_run(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'forecast run'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "run", "run an forecast")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_forecast_validate(subparsers: Subparsers) -> None:
    """
    Subparser for mode: 'forecast validate'

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "validate", "validate an forecast")
    optional = parser.add_argument_group("optional arguments")
    add_arg_quiet(optional)
    add_arg_verbose(optional)


# Dispatch functions.


def dispatch_config(args: Namespace) -> bool:
    """
    Dispatch logic for config mode.

    :param args: Parsed command-line args.
    """
    return {
        "render": dispatch_config_render,
        "translate": dispatch_config_translate,
        "validate": dispatch_config_validate,
    }[args.submode](args)


def dispatch_config_render(args: Namespace) -> bool:
    """
    Dispatch logic for config render submode.

    :param args: Parsed command-line args.
    """
    raise NotImplementedError


def dispatch_config_translate(args: Namespace) -> bool:
    """
    Dispatch logic for config translate submode.

    :param args: Parsed command-line args.
    """
    success = True
    if args.input_format == "atparse" and args.output_format == "jinja2":
        uwtools.config.atparse_to_jinja2.convert(
            input_file=args.input_file, output_file=args.output_file, dry_run=args.dry_run
        )
    else:
        success = False
    return success


def dispatch_config_validate(args: Namespace) -> bool:
    """
    Dispatch logic for config validate submode.

    :param args: Parsed command-line args.
    """
    success = True
    if args.input_format == "yaml":
        success = uwtools.config.validator.validate_yaml(
            config_file=args.input_file, schema_file=args.schema_file
        )
    else:
        success = False
    return success


def dispatch_experiment(args: Namespace) -> bool:
    """
    Dispatch logic for experiment mode.

    :param args: Parsed command-line args.
    """
    return {
        "configure": dispatch_experiment_configure,
        "run": dispatch_experiment_run,
        "validate": dispatch_experiment_validate,
    }[args.submode](args)


def dispatch_experiment_configure(args: Namespace) -> bool:
    """
    Dispatch logic for experiment configure submode.

    :param args: Parsed command-line args.
    """
    raise NotImplementedError


def dispatch_experiment_run(args: Namespace) -> bool:
    """
    Dispatch logic for experiment run submode.

    :param args: Parsed command-line args.
    """
    raise NotImplementedError


def dispatch_experiment_validate(args: Namespace) -> bool:
    """
    Dispatch logic for experiment validate submode.

    :param args: Parsed command-line args.
    """
    raise NotImplementedError


def dispatch_forecast(args: Namespace) -> bool:
    """
    Dispatch logic for forecast mode.

    :param args: Parsed command-line args.
    """
    return {
        "configure": dispatch_forecast_configure,
        "run": dispatch_forecast_run,
        "validate": dispatch_forecast_validate,
    }[args.submode](args)


def dispatch_forecast_configure(args: Namespace) -> bool:
    """
    Dispatch logic for forecast configure submode.

    :param args: Parsed command-line args.
    """
    raise NotImplementedError


def dispatch_forecast_run(args: Namespace) -> bool:
    """
    Dispatch logic for forecast run submode.

    :param args: Parsed command-line args.
    """
    raise NotImplementedError


def dispatch_forecast_validate(args: Namespace) -> bool:
    """
    Dispatch logic for forecast validate submode.

    :param args: Parsed command-line args.
    """
    raise NotImplementedError


# Arguments

# pylint: disable=missing-function-docstring


def add_arg_dry_run(group: Group) -> None:
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="print rendered template only",
    )


def add_arg_input_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        "--input-file",
        "-i",
        help="path to input file (defaults to stdin)",
        metavar="PATH",
        required=required,
        type=str,
    )


def add_arg_input_format(group: Group, choices: List[str]) -> None:
    group.add_argument(
        "--input-format",
        choices=choices,
        help="input-data format",
        required=True,
        type=str,
    )


def add_arg_output_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        "--output-file",
        "-o",
        help="path to output file (defaults to stdout)",
        metavar="PATH",
        required=required,
        type=str,
    )


def add_arg_output_format(group: Group, choices: List[str]) -> None:
    group.add_argument(
        "--output-format",
        choices=choices,
        help="output-data format",
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


def add_arg_schema_file(group: Group) -> None:
    group.add_argument(
        "--schema-file",
        help="path to schema file to use for validation",
        metavar="PATH",
        required=True,
        type=str,
    )


def add_arg_verbose(group: Group) -> None:
    group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="print all logging messages",
    )


# pylint: enable=missing-function-docstring
