"""
Modal CLI.
"""

import datetime as dt
import sys
from argparse import ArgumentParser as Parser
from argparse import HelpFormatter
from argparse import _ArgumentGroup as Group
from argparse import _SubParsersAction as Subparsers
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import uwtools.api.config
import uwtools.api.fv3
import uwtools.api.rocoto
import uwtools.api.sfc_climo_gen
import uwtools.api.template
import uwtools.config.jinja2
import uwtools.rocoto
from uwtools.logging import log, setup_logging
from uwtools.utils.file import FORMAT, get_file_format

FORMATS = list(FORMAT.formats().keys())
TITLE_REQ_ARG = "Required arguments"

Args = Dict[str, Any]
ActionChecks = List[Callable[[Args], Args]]
ModeChecks = Dict[str, ActionChecks]
Checks = Dict[str, ModeChecks]


def main() -> None:
    """
    Main entry point.
    """

    # Silence logging initially, then process the command-line arguments by parsing them. Run all
    # defined checks for the appropriate [sub]mode. Reconfigure logging after quiet/verbose choices
    # are known, then dispatch to the [sub]mode handler.

    setup_logging(quiet=True)
    try:
        args, checks = _parse_args(sys.argv[1:])
        for check in checks[args[STR.mode]][args[STR.action]]:
            check(args)
        setup_logging(quiet=args[STR.quiet], verbose=args[STR.verbose])
        log.debug("Command: %s %s", Path(sys.argv[0]).name, " ".join(sys.argv[1:]))
        modes = {
            STR.config: _dispatch_config,
            STR.fv3: _dispatch_fv3,
            STR.rocoto: _dispatch_rocoto,
            STR.sfcclimogen: _dispatch_sfc_climo_gen,
            STR.template: _dispatch_template,
        }
        sys.exit(0 if modes[args[STR.mode]](args) else 1)
    except Exception as e:  # pylint: disable=broad-exception-caught
        if _switch(STR.debug) in sys.argv:
            log.exception(str(e))
        _abort(str(e))


# Mode config


def _add_subparser_config(subparsers: Subparsers) -> ModeChecks:
    """
    Subparser for mode: config

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.config, "Handle configs")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.action.upper())
    return {
        STR.compare: _add_subparser_config_compare(subparsers),
        STR.realize: _add_subparser_config_realize(subparsers),
        STR.validate: _add_subparser_config_validate(subparsers),
    }


def _add_subparser_config_compare(subparsers: Subparsers) -> ActionChecks:
    """
    Subparser for mode: config compare

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.compare, "Compare configs")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_file_path(required, switch=_switch(STR.file1path), helpmsg="Path to file 1")
    _add_arg_file_path(required, switch=_switch(STR.file2path), helpmsg="Path to file 2")
    optional = _basic_setup(parser)
    _add_arg_file_format(
        optional,
        switch=_switch(STR.file1fmt),
        helpmsg="Format of file 1",
        choices=FORMATS,
    )
    _add_arg_file_format(
        optional,
        switch=_switch(STR.file2fmt),
        helpmsg="Format of file 2",
        choices=FORMATS,
    )
    checks = _add_args_verbosity(optional)
    return checks + [
        partial(_check_file_vs_format, STR.file1path, STR.file1fmt),
        partial(_check_file_vs_format, STR.file2path, STR.file2fmt),
    ]


def _add_subparser_config_realize(subparsers: Subparsers) -> ActionChecks:
    """
    Subparser for mode: config realize

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.realize, "Realize config")
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    _add_arg_input_format(optional, choices=FORMATS)
    _add_arg_output_file(optional)
    _add_arg_output_format(optional, choices=FORMATS)
    _add_arg_values_needed(optional)
    _add_arg_dry_run(optional)
    checks = _add_args_verbosity(optional)
    _add_arg_supplemental_files(optional)
    return checks + [
        partial(_check_file_vs_format, STR.infile, STR.infmt),
        partial(_check_file_vs_format, STR.outfile, STR.outfmt),
    ]


def _add_subparser_config_validate(subparsers: Subparsers) -> ActionChecks:
    """
    Subparser for mode: config validate

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.validate, "Validate config")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_schema_file(required)
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    return _add_args_verbosity(optional)


def _dispatch_config(args: Args) -> bool:
    """
    Dispatch logic for config mode.

    :param args: Parsed command-line args.
    """
    return {
        STR.compare: _dispatch_config_compare,
        STR.realize: _dispatch_config_realize,
        STR.validate: _dispatch_config_validate,
    }[args[STR.action]](args)


def _dispatch_config_compare(args: Args) -> bool:
    """
    Dispatch logic for config compare action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.config.compare(
        config_1_path=args[STR.file1path],
        config_1_format=args[STR.file1fmt],
        config_2_path=args[STR.file2path],
        config_2_format=args[STR.file2fmt],
    )


def _dispatch_config_realize(args: Args) -> bool:
    """
    Dispatch logic for config realize action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.config.realize(
        input_config=args[STR.infile],
        input_format=args[STR.infmt],
        output_file=args[STR.outfile],
        output_format=args[STR.outfmt],
        supplemental_configs=args[STR.suppfiles],
        values_needed=args[STR.valsneeded],
        dry_run=args[STR.dryrun],
    )


def _dispatch_config_validate(args: Args) -> bool:
    """
    Dispatch logic for config validate action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.config.validate(schema_file=args[STR.schemafile], config=args[STR.infile])


# Mode fv3


def _add_subparser_fv3(subparsers: Subparsers) -> ModeChecks:
    """
    Subparser for mode: fv3

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.fv3, "Execute FV3 tasks")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.task.upper())
    return {
        task: _add_subparser_fv3_task(subparsers, task, helpmsg)
        for task, helpmsg in uwtools.api.fv3.tasks().items()
    }


def _add_subparser_fv3_task(subparsers: Subparsers, task: str, helpmsg: str) -> ActionChecks:
    """
    Subparser for mode: fv3 <task>

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    :param task: The task to add a subparser for.
    :param helpmsg: Help message for task.
    """
    parser = _add_subparser(subparsers, task, helpmsg.rstrip("."))
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_config_file(required)
    _add_arg_cycle(required)
    optional = _basic_setup(parser)
    _add_arg_batch(optional)
    _add_arg_dry_run(optional)
    checks = _add_args_verbosity(optional)
    return checks


def _dispatch_fv3(args: Args) -> bool:
    """
    Dispatch logic for fv3 mode.

    :param args: Parsed command-line args.
    """
    return uwtools.api.fv3.execute(
        task=args[STR.action],
        config_file=args[STR.cfgfile],
        cycle=args[STR.cycle],
        batch=args[STR.batch],
        dry_run=args[STR.dryrun],
    )


# Mode rocoto


def _add_subparser_rocoto(subparsers: Subparsers) -> ModeChecks:
    """
    Subparser for mode: rocoto

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.rocoto, "Realize and validate Rocoto XML Documents")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.action.upper())
    return {
        STR.realize: _add_subparser_rocoto_realize(subparsers),
        STR.validate: _add_subparser_rocoto_validate(subparsers),
    }


def _add_subparser_rocoto_realize(subparsers: Subparsers) -> ActionChecks:
    """
    Subparser for mode: rocoto realize

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.realize, "Realize a Rocoto XML workflow document")
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    _add_arg_output_file(optional)
    checks = _add_args_verbosity(optional)
    return checks


def _add_subparser_rocoto_validate(subparsers: Subparsers) -> ActionChecks:
    """
    Subparser for mode: rocoto validate

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.validate, "Validate Rocoto XML")
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    checks = _add_args_verbosity(optional)
    return checks


def _dispatch_rocoto(args: Args) -> bool:
    """
    Dispatch logic for rocoto mode.

    :param args: Parsed command-line args.
    """
    return {
        STR.realize: _dispatch_rocoto_realize,
        STR.validate: _dispatch_rocoto_validate,
    }[
        args[STR.action]
    ](args)


def _dispatch_rocoto_realize(args: Args) -> bool:
    """
    Dispatch logic for rocoto realize action. Validate input and output.

    :param args: Parsed command-line args.
    """
    return uwtools.api.rocoto.realize(config=args[STR.infile], output_file=args[STR.outfile])


def _dispatch_rocoto_validate(args: Args) -> bool:
    """
    Dispatch logic for rocoto validate action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.rocoto.validate(xml_file=args[STR.infile])


# Mode sfc_climo_gen


def _add_subparser_sfc_climo_gen(subparsers: Subparsers) -> ModeChecks:
    """
    Subparser for mode: sfc_climo_gen

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.sfcclimogen, "Execute sfc_climo_gen tasks")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.task.upper())
    return {
        task: _add_subparser_sfc_climo_gen_task(subparsers, task, helpmsg)
        for task, helpmsg in uwtools.api.sfc_climo_gen.tasks().items()
    }


def _add_subparser_sfc_climo_gen_task(
    subparsers: Subparsers, task: str, helpmsg: str
) -> ActionChecks:
    """
    Subparser for mode: sfc_climo_gen <task>

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    :param task: The task to add a subparser for.
    :param helpmsg: Help message for task.
    """
    parser = _add_subparser(subparsers, task, helpmsg.rstrip("."))
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_config_file(required)
    optional = _basic_setup(parser)
    _add_arg_batch(optional)
    _add_arg_dry_run(optional)
    checks = _add_args_verbosity(optional)
    return checks


def _dispatch_sfc_climo_gen(args: Args) -> bool:
    """
    Dispatch logic for sfc_climo_gen mode.

    :param args: Parsed command-line args.
    """
    return uwtools.api.sfc_climo_gen.execute(
        task=args[STR.action],
        config_file=args[STR.cfgfile],
        batch=args[STR.batch],
        dry_run=args[STR.dryrun],
    )


# Mode template


def _add_subparser_template(subparsers: Subparsers) -> ModeChecks:
    """
    Subparser for mode: template

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.template, "Handle templates")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.action.upper())
    return {
        STR.render: _add_subparser_template_render(subparsers),
        STR.translate: _add_subparser_template_translate(subparsers),
    }


def _add_subparser_template_translate(subparsers: Subparsers) -> ActionChecks:
    """
    Subparser for mode: template translate

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.translate, "Translate atparse to Jinja2")
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    _add_arg_output_file(optional)
    _add_arg_dry_run(optional)
    return _add_args_verbosity(optional)


def _add_subparser_template_render(subparsers: Subparsers) -> ActionChecks:
    """
    Subparser for mode: template render

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.render, "Render a template")
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    _add_arg_output_file(optional)
    _add_arg_values_file(optional)
    _add_arg_values_format(optional, choices=FORMATS)
    _add_arg_values_needed(optional)
    _add_arg_partial(optional)
    _add_arg_dry_run(optional)
    checks = _add_args_verbosity(optional)
    _add_arg_key_eq_val_pairs(optional)
    return checks + [_check_template_render_vals_args]


def _dispatch_template(args: Args) -> bool:
    """
    Dispatch logic for template mode.

    :param args: Parsed command-line args.
    """
    return {
        STR.render: _dispatch_template_render,
        STR.translate: _dispatch_template_translate,
    }[
        args[STR.action]
    ](args)


def _dispatch_template_render(args: Args) -> bool:
    """
    Dispatch logic for template render action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.template.render(
        values=args[STR.valsfile],
        values_format=args[STR.valsfmt],
        input_file=args[STR.infile],
        output_file=args[STR.outfile],
        overrides=_dict_from_key_eq_val_strings(args[STR.keyvalpairs]),
        values_needed=args[STR.valsneeded],
        partial=args[STR.partial],
        dry_run=args[STR.dryrun],
    )


def _dispatch_template_translate(args: Args) -> bool:
    """
    Dispatch logic for template translate action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.template.translate(
        input_file=args[STR.infile],
        output_file=args[STR.outfile],
        dry_run=args[STR.dryrun],
    )


# Arguments

# pylint: disable=missing-function-docstring


def _add_arg_batch(group: Group) -> None:
    group.add_argument(
        _switch(STR.batch),
        action="store_true",
        help="Submit run to batch scheduler",
    )


def _add_arg_config_file(group: Group) -> None:
    group.add_argument(
        _switch(STR.cfgfile),
        "-c",
        help="Path to config file",
        metavar="PATH",
        required=True,
        type=Path,
    )


def _add_arg_cycle(group: Group) -> None:
    group.add_argument(
        _switch(STR.cycle),
        help="The cycle in ISO8601 format",
        required=True,
        type=dt.datetime.fromisoformat,
    )


def _add_arg_debug(group: Group) -> None:
    group.add_argument(
        _switch(STR.debug),
        action="store_true",
        help="""
        Print all log messages, plus any unhandled exception's stack trace (implies --verbose)
        """,
    )


def _add_arg_dry_run(group: Group) -> None:
    group.add_argument(
        _switch(STR.dryrun),
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
        type=Path,
    )


def _add_arg_input_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        _switch(STR.infile),
        "-i",
        help="Path to input file (defaults to stdin)",
        metavar="PATH",
        required=required,
        type=Path,
    )


def _add_arg_input_format(group: Group, choices: List[str], required: bool = False) -> None:
    group.add_argument(
        _switch(STR.infmt),
        choices=choices,
        help="Input format",
        required=required,
        type=str,
    )


def _add_arg_key_eq_val_pairs(group: Group) -> None:
    group.add_argument(
        STR.keyvalpairs,
        help="A key=value pair to override/supplement config",
        metavar="KEY=VALUE",
        nargs="*",
    )


def _add_arg_output_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        _switch(STR.outfile),
        "-o",
        help="Path to output file (defaults to stdout)",
        metavar="PATH",
        required=required,
        type=Path,
    )


def _add_arg_output_format(group: Group, choices: List[str], required: bool = False) -> None:
    group.add_argument(
        _switch(STR.outfmt),
        choices=choices,
        help="Output format",
        required=required,
        type=str,
    )


def _add_arg_partial(group: Group) -> None:
    group.add_argument(
        _switch(STR.partial),
        action="store_true",
        help="Permit partial template rendering",
    )


def _add_arg_quiet(group: Group) -> None:
    group.add_argument(
        _switch(STR.quiet),
        "-q",
        action="store_true",
        help="Print no logging messages",
    )


def _add_arg_schema_file(group: Group) -> None:
    group.add_argument(
        _switch(STR.schemafile),
        help="Path to schema file to use for validation",
        metavar="PATH",
        required=True,
        type=Path,
    )


def _add_arg_supplemental_files(group: Group) -> None:
    group.add_argument(
        STR.suppfiles,
        help="Additional files to supplement primary input",
        metavar="PATH",
        nargs="*",
        type=Path,
    )


def _add_arg_values_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        _switch(STR.valsfile),
        help="Path to file providing override or interpolation values",
        metavar="PATH",
        required=required,
        type=Path,
    )


def _add_arg_values_format(group: Group, choices: List[str]) -> None:
    group.add_argument(
        _switch(STR.valsfmt),
        choices=choices,
        help="Values format",
        required=False,
        type=str,
    )


def _add_arg_values_needed(group: Group) -> None:
    group.add_argument(
        _switch(STR.valsneeded),
        action="store_true",
        help="Print report of values needed to render template",
    )


def _add_arg_verbose(group: Group) -> None:
    group.add_argument(
        _switch(STR.verbose),
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


def _add_args_verbosity(group: Group) -> ActionChecks:
    """
    Add debug, quiet, and verbose arguments.

    :param group: The group to add the arguments to.
    :return: Check for mutual exclusivity of quiet/verbose arguments.
    """
    _add_arg_debug(group)
    _add_arg_quiet(group)
    _add_arg_verbose(group)
    return [_check_verbosity]


def _add_subparser(subparsers: Subparsers, name: str, helpmsg: str) -> Parser:
    """
    Add a new subparser, with standard help formatting, to the given parser.

    :param subparsers: The subparsers to add the new subparser to.
    :param name: The name of the subparser.
    :param helpmsg: The help message for the subparser.
    :return: The new subparser.
    """
    parser: Parser = subparsers.add_parser(
        name, add_help=False, help=helpmsg, formatter_class=_formatter, description=helpmsg
    )
    return parser


def _add_subparsers(parser: Parser, dest: str, metavar: str) -> Subparsers:
    """
    Add subparsers to a parser.

    :param parser: The parser to add subparsers to.
    :param dest: Name of parser attribute to store subparser under.
    :param metavar: Name for hierarchy of subparsers as shown by --help.
    :return: The new subparsers object.
    """
    return parser.add_subparsers(
        dest=dest, metavar=metavar, required=True, title="Positional arguments"
    )


def _basic_setup(parser: Parser) -> Group:
    """
    Create optional-arguments group and add help switch.

    :param parser: The parser to add the optional group to.
    """
    optional = parser.add_argument_group("Optional arguments")
    optional.add_argument("-h", _switch(STR.help), action=STR.help, help="Show help and exit")
    return optional


def _check_file_vs_format(file_arg: str, format_arg: str, args: Args) -> Args:
    if args.get(format_arg) is None:
        if args.get(file_arg) is None:
            _abort("Specify %s when %s is not specified" % (_switch(format_arg), _switch(file_arg)))
        args[format_arg] = get_file_format(args[file_arg])
    return args


def _check_template_render_vals_args(args: Args) -> Args:
    # In "template render" mode, a values file is optional, as values used to render the template
    # will be taken from the environment or from key=value command-line pairs by default. But if a
    # values file IS specified, its format must either be explicitly specified, or deduced from its
    # extension.
    if args.get(STR.valsfile) is not None:
        if args.get(STR.valsfmt) is None:
            args[STR.valsfmt] = get_file_format(args[STR.valsfile])
    return args


def _check_verbosity(args: Args) -> Args:
    if args.get(STR.quiet) and (args.get(STR.debug) or args.get(STR.verbose)):
        _abort(
            "%s may not be used with %s or %s"
            % (_switch(STR.quiet), _switch(STR.debug), _switch(STR.verbose))
        )
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
    # max_help_positions sets the maximum starting column for option help text.
    return HelpFormatter(prog, max_help_position=6)


def _parse_args(raw_args: List[str]) -> Tuple[Args, Checks]:
    """
    Parse command-line arguments.

    :param raw_args: The raw command-line arguments to parse.
    :return: Parsed command-line arguments.
    """
    parser = Parser(
        description="Unified Workflow Tools", add_help=False, formatter_class=_formatter
    )
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.mode, STR.mode.upper())
    checks = {
        STR.config: _add_subparser_config(subparsers),
        STR.fv3: _add_subparser_fv3(subparsers),
        STR.rocoto: _add_subparser_rocoto(subparsers),
        STR.sfcclimogen: _add_subparser_sfc_climo_gen(subparsers),
        STR.template: _add_subparser_template(subparsers),
    }
    return vars(parser.parse_args(raw_args)), checks


def _switch(arg: str) -> str:
    """
    Convert argument name to long-form switch.

    :param arg: Internal name of parsed argument.
    :return: The long-form switch.
    """
    return "--%s" % arg.replace("_", "-")


@dataclass(frozen=True)
class STR:
    """
    A lookup map for CLI-related strings.
    """

    action: str = "action"
    batch: str = "batch"
    cfgfile: str = "config_file"
    compare: str = "compare"
    config: str = "config"
    cycle: str = "cycle"
    debug: str = "debug"
    dryrun: str = "dry_run"
    file1fmt: str = "file_1_format"
    file1path: str = "file_1_path"
    file2fmt: str = "file_2_format"
    file2path: str = "file_2_path"
    fv3: str = "fv3"
    help: str = "help"
    infile: str = "input_file"
    infmt: str = "input_format"
    keyvalpairs: str = "key_eq_val_pairs"
    mode: str = "mode"
    model: str = "model"
    outfile: str = "output_file"
    outfmt: str = "output_format"
    partial: str = "partial"
    quiet: str = "quiet"
    realize: str = "realize"
    render: str = "render"
    rocoto: str = "rocoto"
    run: str = "run"
    schemafile: str = "schema_file"
    sfcclimogen: str = "sfc_climo_gen"
    suppfiles: str = "supplemental_files"
    task: str = "task"
    tasks: str = "tasks"
    template: str = "template"
    translate: str = "translate"
    validate: str = "validate"
    valsfile: str = "values_file"
    valsfmt: str = "values_format"
    valsneeded: str = "values_needed"
    verbose: str = "verbose"
