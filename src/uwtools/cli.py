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
from uwtools.utils.file import FORMAT, get_file_type

FORMATS = [FORMAT.ini, FORMAT.nml, FORMAT.yaml]
TITLE_REQ_ARG = "Required arguments"


def main() -> None:
    """
    Main entry point.
    """

    # Silence logging initially, then process the command-line arguments by parsing them, filling
    # in any unspecified data-format arguments, and checking semantic argument validity (i.e. that
    # the arguments make sense together, not just on their own). If the arguments are sane, set up
    # logging correctly, then dispatch to the mode handler, which will the dispatch to the submode
    # handler. Shield command-line users from raised exceptions by aborting gracefully.

    setup_logging(quiet=True)
    modes = {
        "config": _dispatch_config,
        "forecast": _dispatch_forecast,
        "template": _dispatch_template,
    }
    try:
        args = _check_args(_set_formats(_parse_args(sys.argv[1:])))
        setup_logging(quiet=args.quiet, verbose=args.verbose)
        sys.exit(0 if modes[args.mode](args) else 1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        _abort(str(e))


# Mode config


def _add_subparser_config(subparsers: Subparsers) -> None:
    """
    Subparser for mode: config

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, "config", "Handle configs")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, "submode")
    _add_subparser_config_compare(subparsers)
    _add_subparser_config_realize(subparsers)
    _add_subparser_config_translate(subparsers)
    _add_subparser_config_validate(subparsers)


def _add_subparser_config_compare(subparsers: Subparsers) -> None:
    """
    Subparser for mode: config compare

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, "compare", "Compare configs")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_file_path(required, switch="--file-1-path", helpmsg="Path to file 1")
    _add_arg_file_path(required, switch="--file-2-path", helpmsg="Path to file 2")
    optional = _basic_setup(parser)
    _add_arg_file_format(
        optional,
        switch="--file-1-format",
        helpmsg="Format of file 1",
        choices=FORMATS,
    )
    _add_arg_file_format(
        optional,
        switch="--file-2-format",
        helpmsg="Format of file 2",
        choices=FORMATS,
    )
    basic_setup(parser)


def _add_subparser_config_realize(subparsers: Subparsers) -> None:
    """
    Subparser for mode: config realize

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, "realize", "Realize config")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_values_file(required, required=True)
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    _add_arg_input_format(optional, choices=FORMATS)
    _add_arg_output_file(optional)
    _add_arg_output_format(optional, choices=FORMATS)
    _add_arg_values_format(optional, choices=FORMATS)
    _add_arg_values_needed(optional)
    _add_arg_dry_run(optional)


def _add_subparser_config_translate(subparsers: Subparsers) -> None:
    """
    Subparser for mode: config translate

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, "translate", "Translate configs")
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    _add_arg_input_format(optional, choices=[FORMAT.atparse])
    _add_arg_output_file(optional)
    _add_arg_output_format(optional, choices=[FORMAT.jinja2])
    _add_arg_dry_run(optional)


def _add_subparser_config_validate(subparsers: Subparsers) -> None:
    """
    Subparser for mode: config validate

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, "validate", "Validate config")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_schema_file(required)
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    _add_arg_input_format(optional, choices=[FORMAT.yaml])


def _dispatch_config(args: Namespace) -> bool:
    """
    Dispatch logic for config mode.

    :param args: Parsed command-line args.
    """
    return {
        "compare": _dispatch_config_compare,
        "realize": _dispatch_config_realize,
        "translate": _dispatch_config_translate,
        "validate": _dispatch_config_validate,
    }[args.submode](args)


def _dispatch_config_compare(args: Namespace) -> bool:
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


def _dispatch_config_realize(args: Namespace) -> bool:
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


def _dispatch_config_translate(args: Namespace) -> bool:
    """
    Dispatch logic for config translate submode.

    :param args: Parsed command-line args.
    """
    success = True
    if args.input_format == FORMAT.atparse and args.output_format == FORMAT.jinja2:
        uwtools.config.atparse_to_jinja2.convert(
            input_file=args.input_file, output_file=args.output_file, dry_run=args.dry_run
        )
    else:
        success = False
    return success


def _dispatch_config_validate(args: Namespace) -> bool:
    """
    Dispatch logic for config validate submode.

    :param args: Parsed command-line args.
    """
    success = True
    if args.input_format == FORMAT.yaml:
        success = uwtools.config.validator.validate_yaml(
            config_file=args.input_file, schema_file=args.schema_file
        )
    else:
        success = False
    return success


# Mode forecast


def _add_subparser_forecast(subparsers: Subparsers) -> None:
    """
    Subparser for mode: forecast

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, "forecast", "Configure and run forecasts")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, "submode")
    _add_subparser_forecast_run(subparsers)


def _add_subparser_forecast_run(subparsers: Subparsers) -> None:
    """
    Subparser for mode: forecast run

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, "run", "Run a forecast")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_config_file(required)
    _add_arg_model(required, choices=["FV3"])
    optional = _basic_setup(parser)
    _add_arg_dry_run(optional)


def _dispatch_forecast(args: Namespace) -> bool:
    """
    Dispatch logic for forecast mode.

    :param args: Parsed command-line args.
    """
    return {"run": _dispatch_forecast_run}[args.submode](args)


def _dispatch_forecast_run(args: Namespace) -> bool:
    """
    Dispatch logic for forecast run submode.

    :param args: Parsed command-line args.
    """
    forecast_class = uwtools.drivers.forecast.CLASSES[args.forecast_model]
    forecast_class(config_file=args.config_file).run()
    return True


# Mode template


def _add_subparser_template(subparsers: Subparsers) -> None:
    """
    Subparser for mode: template

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, "template", "Handle templates")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, "submode")
    _add_subparser_template_render(subparsers)


def _add_subparser_template_render(subparsers: Subparsers) -> None:
    """
    Subparser for mode: template render

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, "render", "Render a template")
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    _add_arg_output_file(optional)
    _add_arg_values_file(optional)
    _add_arg_values_format(optional, choices=FORMATS)
    _add_arg_values_needed(optional)
    _add_arg_dry_run(optional)
    _add_arg_key_eq_val_pairs(optional)


def _dispatch_template(args: Namespace) -> bool:
    """
    Dispatch logic for template mode.

    :param args: Parsed command-line args.
    """
    return {"render": _dispatch_template_render}[args.submode](args)


def _dispatch_template_render(args: Namespace) -> bool:
    """
    Dispatch logic for template render submode.

    :param args: Parsed command-line args.
    """
    logging.debug("Command: %s %s", Path(sys.argv[0]).name, " ".join(sys.argv[1:]))
    return uwtools.config.templater.render(
        input_file=args.input_file,
        output_file=args.output_file,
        values_file=args.values_file,
        values_format=args.values_format,
        overrides=_dict_from_key_eq_val_strings(args.key_eq_val_pairs),
        values_needed=args.values_needed,
        dry_run=args.dry_run,
    )


# Arguments

# pylint: disable=missing-function-docstring


def _add_arg_config_file(group: Group) -> None:
    group.add_argument(
        "--config-file",
        "-c",
        help="Path to config file",
        metavar="PATH",
        required=True,
        type=str,
    )


def _add_arg_dry_run(group: Group) -> None:
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Only log info, making no changes",
    )


def _add_arg_file_format(
    group: Group, switch: str, helpmsg: str, choices: List[str], required: bool = False
) -> None:
    group.add_argument(
        switch,
        choices=choices,
        help=helpmsg,
        required=required,
        type=str,
    )


def _add_arg_file_path(group: Group, switch: str, helpmsg: str, required: bool = True) -> None:
    group.add_argument(
        switch,
        help=helpmsg,
        metavar="PATH",
        required=required,
        type=str,
    )


def _add_arg_input_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        "--input-file",
        "-i",
        help="Path to input file (defaults to stdin)",
        metavar="PATH",
        required=required,
        type=str,
    )


def _add_arg_input_format(group: Group, choices: List[str], required: bool = False) -> None:
    group.add_argument(
        "--input-format",
        choices=choices,
        help="Input format",
        required=required,
        type=str,
    )


def _add_arg_key_eq_val_pairs(group: Group) -> None:
    group.add_argument(
        "key_eq_val_pairs",
        help="A key=value pair to override/supplement config",
        metavar="KEY=VALUE",
        nargs="*",
    )


def _add_arg_model(group: Group, choices: List[str]) -> None:
    group.add_argument(
        "--model",
        choices=choices,
        help="Model name",
        required=True,
        type=str,
    )


def _add_arg_output_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        "--output-file",
        "-o",
        help="Path to output file (defaults to stdout)",
        metavar="PATH",
        required=required,
        type=str,
    )


def _add_arg_output_format(group: Group, choices: List[str], required: bool = False) -> None:
    group.add_argument(
        "--output-format",
        choices=choices,
        help="Output format",
        required=required,
        type=str,
    )


def _add_arg_quiet(group: Group) -> None:
    group.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Print no logging messages",
    )


def _add_arg_schema_file(group: Group) -> None:
    group.add_argument(
        "--schema-file",
        help="Path to schema file to use for validation",
        metavar="PATH",
        required=True,
        type=str,
    )


def _add_arg_values_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        "--values-file",
        help="Path to file providing override or interpolation values",
        metavar="PATH",
        required=required,
        type=str,
    )


def _add_arg_values_format(group: Group, choices: List[str]) -> None:
    group.add_argument(
        "--values-format",
        choices=choices,
        help="Values format",
        required=False,
        type=str,
    )


def _add_arg_values_needed(group: Group) -> None:
    group.add_argument(
        "--values-needed",
        action="store_true",
        help="Print report of values needed to render template",
    )


def _add_arg_verbose(group: Group) -> None:
    group.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print all logging messages",
    )


# pylint: enable=missing-function-docstring


# Support


def _abort(msg: str) -> None:
    """
    Exit with an informative message and error status.

    :param msg: The message to print.
    """
    print(msg, file=sys.stderr)
    sys.exit(1)


def _add_subparser(subparsers: Subparsers, name: str, helpmsg: str) -> Parser:
    """
    Add a new subparser, with standard help formatting, to the given parser.

    :param subparsers: The subparsers to add the new subparser to.
    :param name: The name of the subparser.
    :param helpmsg: The help message for the subparser.
    :return: The new subparser.
    """
    return subparsers.add_parser(
        name, add_help=False, help=helpmsg, formatter_class=_formatter, description=helpmsg
    )


def _add_subparsers(parser: Parser, dest: str) -> Subparsers:
    """
    Add subparsers to a parser.

    :parm parser: The parser to add subparsers to.
    :return: The new subparsers object.
    """
    return parser.add_subparsers(
        dest=dest, metavar="MODE", required=True, title="Positional arguments"
    )


def _basic_setup(parser: Parser) -> Group:
    """
    Create optional-arguments group and add help switch.

    :param parser: The parser to add the optional group to.
    """
    optional = parser.add_argument_group("Optional arguments")
    optional.add_argument("-h", "--help", action="help", help="Show help and exit")
    add_arg_quiet(optional)
    add_arg_verbose(optional)
    return optional


def _check_args(args: Namespace) -> Namespace:
    """
    Validate basic argument correctness.

    :param args: The parsed command-line arguments to check.
    :return: The checked command-line arguments.
    :raises: SystemExit if any checks failed.
    """
    a = vars(args)
    if a.get("quiet") and a.get("verbose"):
        _abort("Specify at most one of --quiet, --verbose")
    if a.get("values_file") and not a.get("values_format"):
        _abort("Specify --values-format with --values-file")
    return args


def _dict_from_key_eq_val_strings(config_items: List[str]) -> Dict[str, str]:
    """
    Given a list of key=value strings, return a dictionary of key/value pairs.

    :param config_items: Strings in the form key=value.
    :return: A dictionary based on the input key=value strings.
    """
    return dict([arg.split("=") for arg in config_items])


def _formatter(prog: str) -> HelpFormatter:
    """
    A standard formatter for help messages.
    """
    return HelpFormatter(prog, max_help_position=8)


def _parse_args(raw_args: List[str]) -> Namespace:
    """
    Parse command-line arguments.

    :param raw_args: The raw command-line arguments to parse.
    :return: Parsed command-line arguments.
    """

    parser = Parser(
        description="Unified Workflow Tools", add_help=False, formatter_class=_formatter
    )
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, "mode")
    _add_subparser_config(subparsers)
    _add_subparser_forecast(subparsers)
    _add_subparser_template(subparsers)
    return parser.parse_args(raw_args)


def _set_formats(args: Namespace) -> Namespace:
    """
    Try to set missing format information.

    :param args: The parsed command-line arguments.
    :return: The parsed command-line arguments with missing formats set, when possible.
    :raises: SystemExit if any missing format cannot be deduced.
    """

    # Loop over pairs of path/format argument attributes and, for each, check if the path attribute
    # is present (but possibly set to None), to decide if the pair is used in the current [sub]mode.
    # If so, and if the format attribute was explicitly set on the command line, all's well; but if
    # the format attribute is not set, try to set it now after deducing it from the path's extension
    # and abort if this is not possible -- either because the path attribute is not set, or because
    # the extension is unrecognized.

    switch = lambda x: "--%s" % x.replace("_", "-")
    attrs = vars(args)
    path2fmt = {
        "file_1_path": "file_1_format",
        "file_2_path": "file_2_format",
        "input_file": "input_format",
        "output_file": "output_format",
        "values_file": "values_format",
    }
    for path_attr, fmt_attr in path2fmt.items():
        if path_attr in attrs:
            if attrs[fmt_attr] is None:
                if attrs[path_attr] is None:
                    _abort(
                        "Specify %s when %s is not specified"
                        % (switch(fmt_attr), switch(path_attr))
                    )
                attrs[fmt_attr] = get_file_type(attrs[path_attr])
    return args
