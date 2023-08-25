"""
Modal CLI.
"""

import logging
import sys
from argparse import ArgumentParser as Parser
from argparse import HelpFormatter, Namespace
from argparse import _ArgumentGroup as Group
from argparse import _SubParsersAction as Subparsers
from pathlib import Path
from typing import List

import uwtools.config.atparse_to_jinja2
import uwtools.config.templater
import uwtools.config.validator
from uwtools.logging import setup_logging

TITLE_REQ_ARG = "Required arguments"

# Main entry point


def main() -> None:
    """
    Main entry point.
    """
    args = check_args(parse_args(sys.argv[1:]))
    setup_logging(quiet=args.quiet, verbose=args.verbose)
    modes = {
        "config": dispatch_config,
        # "experiment": dispatch_experiment,
        # "forecast": dispatch_forecast,
        "template": dispatch_template,
    }
    success = modes[args.mode](args)
    sys.exit(0 if success else 1)


# Mode config


def add_subparser_config(subparsers: Subparsers) -> None:
    """
    Subparser for mode: config

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "config", "Work with config files")
    basic_setup(parser)
    subparsers = add_subparsers(parser, "submode")
    add_subparser_config_render(subparsers)
    add_subparser_config_translate(subparsers)
    add_subparser_config_validate(subparsers)


def add_subparser_config_render(subparsers: Subparsers) -> None:
    """
    Subparser for mode: config render

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "render", "Render config files")
    optional = basic_setup(parser)
    add_arg_input_file(optional)
    add_arg_output_file(optional)
    add_arg_config_file(optional)
    add_arg_values_needed(optional)
    add_arg_dry_run(optional)
    add_arg_quiet(optional)
    add_arg_verbose(optional)
    add_arg_key_eq_val_pairs(optional)


def add_subparser_config_translate(subparsers: Subparsers) -> None:
    """
    Subparser for mode: config translate

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "translate", "Translate config files")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    add_arg_input_format(required, choices=["atparse"])
    add_arg_output_format(required, choices=["jinja2"])
    optional = basic_setup(parser)
    add_arg_input_file(optional)
    add_arg_output_file(optional)
    add_arg_dry_run(optional)
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_config_validate(subparsers: Subparsers) -> None:
    """
    Subparser for mode: config validate

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "validate", "Validate config files")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    add_arg_input_format(required, choices=["yaml"])
    add_arg_schema_file(required)
    optional = basic_setup(parser)
    add_arg_input_file(optional)
    add_arg_quiet(optional)
    add_arg_verbose(optional)


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


# Mode experiment


# def add_subparser_experiment(subparsers: Subparsers) -> None:
#    """
#    Subparser for mode: experiment
#
#    :param subparsers: Parent parser's subparsers, to add this subparser to.
#    """
#    parser = add_subparser(subparsers, "experiment", "Manage experiments")
#    parser.add_argument('-h', '--help', action='help', dest='help', help="Show help and exit")
#    subparsers = add_subparsers(parser, dest="submode")
#    add_subparser_experiment_configure(subparsers)
#    add_subparser_experiment_run(subparsers)
#    add_subparser_experiment_validate(subparsers)


# def add_subparser_experiment_configure(subparsers: Subparsers) -> None:
#    """
#    Subparser for mode: experiment configure
#
#    :param subparsers: Parent parser's subparsers, to add this subparser to.
#    """
#    parser = add_subparser(subparsers, "configure", "Configure an experiment")
#    parser.add_argument('-h', '--help', action='help', dest='help', help="Show help and exit")
#    optional = basic_setup(parser)
#    add_arg_quiet(optional)
#    add_arg_verbose(optional)


# def add_subparser_experiment_run(subparsers: Subparsers) -> None:
#    """
#    Subparser for mode: experiment run
#
#    :param subparsers: Parent parser's subparsers, to add this subparser to.
#    """
#    parser = add_subparser(subparsers, "run", "Run an experiment")
#    parser.add_argument('-h', '--help', action='help', dest='help', help="Show help and exit")
#    optional = basic_setup(parser)
#    add_arg_quiet(optional)
#    add_arg_verbose(optional)


# def add_subparser_experiment_validate(subparsers: Subparsers) -> None:
#    """
#    Subparser for mode: experiment validate
#
#    :param subparsers: Parent parser's subparsers, to add this subparser to.
#    """
#    parser = add_subparser(subparsers, "validate", "Validate an experiment")
#    parser.add_argument('-h', '--help', action='help', dest='help', help="Show help and exit")
#    optional = basic_setup(parser)
#    add_arg_quiet(optional)
#    add_arg_verbose(optional)


# def dispatch_experiment(args: Namespace) -> bool:
#    """
#    Dispatch logic for experiment mode.
#
#    :param args: Parsed command-line args.
#    """
#    return {
#        "configure": dispatch_experiment_configure,
#        "run": dispatch_experiment_run,
#        "validate": dispatch_experiment_validate,
#    }[args.submode](args)


# def dispatch_experiment_configure(args: Namespace) -> bool:
#    """
#    Dispatch logic for experiment configure submode.
#
#    :param args: Parsed command-line args.
#    """
#    raise NotImplementedError


# def dispatch_experiment_run(args: Namespace) -> bool:
#    """
#    Dispatch logic for experiment run submode.
#
#    :param args: Parsed command-line args.
#    """
#    raise NotImplementedError


# def dispatch_experiment_validate(args: Namespace) -> bool:
#    """
#    Dispatch logic for experiment validate submode.
#
#    :param args: Parsed command-line args.
#    """
#    raise NotImplementedError


# Mode forecast


# def add_subparser_forecast(subparsers: Subparsers) -> None:
#    """
#    Subparser for mode: forecast
#
#    :param subparsers: Parent parser's subparsers, to add this subparser to.
#    """
#    parser = add_subparser(subparsers, "forecast", "Configure and run forecasts")
#    basic_setup(parser)
#    subparsers = add_subparsers(parser, "submode")
#    add_subparser_forecast_run(subparsers)


# def add_subparser_forecast_run(subparsers: Subparsers) -> None:
#    """
#    Subparser for mode: forecast run
#
#    :param subparsers: Parent parser's subparsers, to add this subparser to.
#    """
#    parser = add_subparser(subparsers, "run", "Run a forecast")
#    optional = basic_setup(parser)
#    add_arg_quiet(optional)
#    add_arg_verbose(optional)


# def dispatch_forecast(args: Namespace) -> bool:
#    """
#    Dispatch logic for forecast mode.
#
#    :param args: Parsed command-line args.
#    """
#    return {"run": dispatch_forecast_run}[args.submode](args)


# def dispatch_forecast_run(args: Namespace) -> bool:
#    """
#    Dispatch logic for forecast run submode.
#
#    :param args: Parsed command-line args.
#    """
#    raise NotImplementedError


# Mode template


def add_subparser_template(subparsers: Subparsers) -> None:
    """
    Subparser for mode: template

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "template", "Manipulate Jinja2 templates")
    basic_setup(parser)
    subparsers = add_subparsers(parser, "submode")
    add_subparser_template_render(subparsers)


def add_subparser_template_render(subparsers: Subparsers) -> None:
    """
    Subparser for mode: template render

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "render", "Render a Jina2 template")
    optional = basic_setup(parser)
    add_arg_input_file(optional)
    add_arg_output_file(optional)
    add_arg_config_file(optional)
    add_arg_values_needed(optional)
    add_arg_dry_run(optional)
    add_arg_quiet(optional)
    add_arg_verbose(optional)
    add_arg_key_eq_val_pairs(optional)


def dispatch_template(args: Namespace) -> bool:
    """
    Dispatch logic for template mode.

    :param args: Parsed command-line args.
    """
    return {"render": dispatch_template_render}[args.submode](args)


def dispatch_template_render(args: Namespace) -> bool:
    """
    Dispatch logic for template render submode.

    :param args: Parsed command-line args.
    """
    logging.debug("Command: %s %s", Path(sys.argv[0]).name, " ".join(sys.argv[1:]))
    return uwtools.config.templater.render(
        args.input_file,
        args.output_file,
        args.config_file,
        args.key_eq_val_pairs,
        args.values_needed,
        args.dry_run,
    )


# Arguments

# pylint: disable=missing-function-docstring


def add_arg_config_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        "--config-file",
        "-c",
        help="Path to config file",
        metavar="PATH",
        required=required,
        type=str,
    )


def add_arg_dry_run(group: Group) -> None:
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Print rendered template only",
    )


def add_arg_input_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        "--input-file",
        "-i",
        help="Path to input file (defaults to stdin)",
        metavar="PATH",
        required=required,
        type=str,
    )


def add_arg_input_format(group: Group, choices: List[str]) -> None:
    group.add_argument(
        "--input-format",
        choices=choices,
        help="Input-data format",
        required=True,
        type=str,
    )


def add_arg_key_eq_val_pairs(group: Group) -> None:
    group.add_argument(
        "key_eq_val_pairs",
        help="A key=value pair to override/supplement config",
        metavar="KEY=VALUE",
        nargs="*",
    )


def add_arg_output_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        "--output-file",
        "-o",
        help="Path to output file (defaults to stdout)",
        metavar="PATH",
        required=required,
        type=str,
    )


def add_arg_output_format(group: Group, choices: List[str]) -> None:
    group.add_argument(
        "--output-format",
        choices=choices,
        help="Output-data format",
        required=True,
        type=str,
    )


def add_arg_quiet(group: Group) -> None:
    group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Print no logging messages",
    )


def add_arg_schema_file(group: Group) -> None:
    group.add_argument(
        "--schema-file",
        help="Path to schema file to use for validation",
        metavar="PATH",
        required=True,
        type=str,
    )


def add_arg_values_needed(group: Group) -> None:
    group.add_argument(
        "--values-needed",
        action="store_true",
        help="Print report of values needed to render template",
    )


def add_arg_verbose(group: Group) -> None:
    group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print all logging messages",
    )


# pylint: enable=missing-function-docstring


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
    return subparsers.add_parser(
        name, add_help=False, help=msg, formatter_class=formatter, description=msg
    )


def add_subparsers(parser: Parser, dest: str) -> Subparsers:
    """
    Add subparsers to a parser.

    :parm parser: The parser to add subparsers to.
    :return: The new subparsers object.
    """
    return parser.add_subparsers(
        dest=dest, metavar="MODE", required=True, title="Positional arguments"
    )


def basic_setup(parser: Parser) -> Group:
    """
    Create optional-arguments group and add help switch.

    :param parser: The parser to add the optional group to.
    """
    optional = parser.add_argument_group("Optional arguments")
    optional.add_argument("-h", "--help", action="help", help="Show help and exit")
    return optional


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


def formatter(prog: str) -> HelpFormatter:
    """
    A standard formatter for help messages.
    """
    return HelpFormatter(prog, max_help_position=8)


def parse_args(raw_args: List[str]) -> Namespace:
    """
    Parse command-line arguments.

    :param raw_args: The raw command-line arguments to parse.
    :return: Parsed command-line arguments.
    """

    parser = Parser(description="Unified Workflow Tools", add_help=False, formatter_class=formatter)
    basic_setup(parser)
    subparsers = add_subparsers(parser, "mode")
    add_subparser_config(subparsers)
    # add_subparser_experiment(subparsers)
    # add_subparser_forecast(subparsers)
    add_subparser_template(subparsers)
    return parser.parse_args(raw_args)
