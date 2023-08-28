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
from typing import Dict, List

import uwtools.config.atparse_to_jinja2
import uwtools.config.core
import uwtools.config.templater
import uwtools.config.validator
import uwtools.drivers.forecast
from uwtools.logging import setup_logging

TITLE_REQ_ARG = "Required arguments"


def main() -> None:
    """
    Main entry point.
    """
    args = check_args(parse_args(sys.argv[1:]))
    setup_logging(quiet=args.quiet, verbose=args.verbose)
    modes = {
        "config": dispatch_config,
        "forecast": dispatch_forecast,
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
    parser = add_subparser(subparsers, "config", "Handle configs")
    basic_setup(parser)
    subparsers = add_subparsers(parser, "submode")
    add_subparser_config_compare(subparsers)
    add_subparser_config_realize(subparsers)
    add_subparser_config_translate(subparsers)
    add_subparser_config_validate(subparsers)


def add_subparser_config_compare(subparsers: Subparsers) -> None:
    """
    Subparser for mode: config compare

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    choices = ["ini", "nml", "yaml"]
    parser = add_subparser(subparsers, "compare", "Compare configs")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    add_arg_file_path(required, switch="--file-1-path", helpmsg="Path to config file 1")
    add_arg_file_format(
        required,
        switch="--file-1-format",
        helpmsg="Format of config file 1",
        choices=choices,
    )
    add_arg_file_path(required, switch="--file-2-path", helpmsg="Path to config file 2")
    add_arg_file_format(
        required,
        switch="--file-2-format",
        helpmsg="Format of config file 2",
        choices=choices,
    )
    optional = basic_setup(parser)
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_config_realize(subparsers: Subparsers) -> None:
    """
    Subparser for mode: config realize

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    choices = ["ini", "nml", "yaml"]
    parser = add_subparser(subparsers, "realize", "Realize config")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    add_arg_input_format(required, choices=choices)
    add_arg_output_format(required, choices=choices)
    optional = basic_setup(parser)
    add_arg_input_file(optional)
    add_arg_output_file(optional)
    add_arg_values_file(optional)
    add_arg_values_format(optional, choices=choices)
    add_arg_values_needed(optional)
    add_arg_dry_run(optional)
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def add_subparser_config_translate(subparsers: Subparsers) -> None:
    """
    Subparser for mode: config translate

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "translate", "Translate configs")
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
    parser = add_subparser(subparsers, "validate", "Validate config")
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
        "compare": dispatch_config_compare,
        "realize": dispatch_config_realize,
        "translate": dispatch_config_translate,
        "validate": dispatch_config_validate,
    }[args.submode](args)


def dispatch_config_compare(args: Namespace) -> bool:
    """
    Dispatch logic for config compare submode.

    :param args: Parsed command-line args.
    """
    return uwtools.config.core.compare_configs(
        config_a_path=args.file_1_path,
        config_a_format=args.file_1_format,
        config_b_path=args.file_2_path,
        config_b_format=args.file_2_format,
    )


def dispatch_config_realize(args: Namespace) -> bool:
    """
    Dispatch logic for config realize submode.

    :param args: Parsed command-line args.
    """
    return uwtools.config.core.realize_config(
        input_file=args.input_file,
        input_format=args.input_format,
        output_file=args.output_file,
        output_format=args.output_format,
        values_file=args.values_file,
        values_format=args.values_format,
        values_needed=args.values_needed,
        dry_run=args.dry_run,
    )


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


# Mode forecast


def add_subparser_forecast(subparsers: Subparsers) -> None:
    """
    Subparser for mode: forecast

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "forecast", "Configure and run forecasts")
    basic_setup(parser)
    subparsers = add_subparsers(parser, "submode")
    add_subparser_forecast_run(subparsers)


def add_subparser_forecast_run(subparsers: Subparsers) -> None:
    """
    Subparser for mode: forecast run

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "run", "Run a forecast")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    add_arg_config_file(required)
    add_arg_model(required, choices=["FV3"])
    optional = basic_setup(parser)
    add_arg_dry_run(optional)
    add_arg_quiet(optional)
    add_arg_verbose(optional)


def dispatch_forecast(args: Namespace) -> bool:
    """
    Dispatch logic for forecast mode.

    :param args: Parsed command-line args.
    """
    return {"run": dispatch_forecast_run}[args.submode](args)


def dispatch_forecast_run(args: Namespace) -> bool:
    """
    Dispatch logic for forecast run submode.

    :param args: Parsed command-line args.
    """
    forecast_class = uwtools.drivers.forecast.CLASSES[args.forecast_model]
    forecast_class(config_file=args.config_file).run()
    return True


# Mode template


def add_subparser_template(subparsers: Subparsers) -> None:
    """
    Subparser for mode: template

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "template", "Handle templates")
    basic_setup(parser)
    subparsers = add_subparsers(parser, "submode")
    add_subparser_template_render(subparsers)


def add_subparser_template_render(subparsers: Subparsers) -> None:
    """
    Subparser for mode: template render

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = add_subparser(subparsers, "render", "Render a template")
    optional = basic_setup(parser)
    add_arg_input_file(optional)
    add_arg_output_file(optional)
    add_arg_values_file(optional)
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
        input_file=args.input_file,
        output_file=args.output_file,
        values_file=args.values_file,
        overrides=dict_from_key_eq_val_strings(args.key_eq_val_pairs),
        values_needed=args.values_needed,
        dry_run=args.dry_run,
    )


# Arguments

# pylint: disable=missing-function-docstring


def add_arg_compare(group: Group) -> None:
    group.add_argument(
        "--compare",
        action="store_true",
        help="Compare two configs",
    )


def add_arg_config_file(group: Group) -> None:
    group.add_argument(
        "--config-file",
        "-c",
        help="Path to YAML config file",
        metavar="PATH",
        required=True,
        type=str,
    )


def add_arg_dry_run(group: Group) -> None:
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Print rendered template only",
    )


def add_arg_file_format(
    group: Group, switch: str, helpmsg: str, choices: List[str], required: bool = False
) -> None:
    group.add_argument(
        switch,
        choices=choices,
        help=helpmsg,
        required=required,
        type=str,
    )


def add_arg_file_path(group: Group, switch: str, helpmsg: str, required: bool = True) -> None:
    group.add_argument(
        switch,
        help=helpmsg,
        metavar="PATH",
        required=required,
        type=str,
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
        help="Input format",
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


def add_arg_model(group: Group, choices: List[str]) -> None:
    group.add_argument(
        "--model",
        choices=choices,
        help="Model name",
        required=True,
        type=str,
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
        help="Output format",
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


def add_arg_values_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        "--values-file",
        help="Path to file providing override or interpolation values",
        metavar="PATH",
        required=required,
        type=str,
    )


def add_arg_values_format(group: Group, choices: List[str], required: bool = False) -> None:
    group.add_argument(
        "--values-format",
        choices=choices,
        help="Values format",
        required=required,
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


def add_subparser(subparsers: Subparsers, name: str, helpmsg: str) -> Parser:
    """
    Add a new subparser, with standard help formatting, to the given parser.

    :param subparsers: The subparsers to add the new subparser to.
    :param name: The name of the subparser.
    :param helpmsg: The help message for the subparser.
    :return: The new subparser.
    """
    return subparsers.add_parser(
        name, add_help=False, help=helpmsg, formatter_class=formatter, description=helpmsg
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
    try:
        if args.values_file and not args.values_format:
            abort("Specify --values-format with --values-file")
    except AttributeError:
        pass
    return args


def dict_from_key_eq_val_strings(config_items: List[str]) -> Dict[str, str]:
    """
    Given a list of key=value strings, return a dictionary of key/value pairs.

    :param config_items: Strings in the form key=value.
    :return: A dictionary based on the input key=value strings.
    """
    return dict([arg.split("=") for arg in config_items])


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
    add_subparser_forecast(subparsers)
    add_subparser_template(subparsers)
    return parser.parse_args(raw_args)
