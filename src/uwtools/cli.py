"""
Modal CLI.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from argparse import ArgumentParser as Parser
from argparse import HelpFormatter
from argparse import _ArgumentGroup as Group
from argparse import _SubParsersAction as Subparsers
from functools import partial
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, NoReturn

import uwtools.api
import uwtools.api.config
import uwtools.api.driver
import uwtools.api.execute
import uwtools.api.fs
import uwtools.api.rocoto
import uwtools.api.template
import uwtools.config.jinja2
import uwtools.rocoto
from uwtools.exceptions import UWConfigRealizeError, UWError, UWTemplateRenderError
from uwtools.logging import log, setup_logging
from uwtools.strings import FORMAT, STR
from uwtools.utils.file import get_config_format, resource_path

FORMATS = FORMAT.extensions()
LEADTIME_DESC = "hours[:minutes[:seconds]]"
TITLE_REQ_ARG = "Required arguments"

Args = dict[str, Any]
ActionChecks = list[Callable[[Args], Args]]
ModeChecks = dict[str, ActionChecks]
Checks = dict[str, ModeChecks]


def main() -> None:
    """
    Main entry point.
    """

    # Silence logging initially, then process the command-line arguments by parsing them. Run all
    # defined checks for the appropriate [sub]mode. Reconfigure logging after quiet/verbose choices
    # are known, then dispatch to the [sub]mode handler.

    try:
        setup_logging(quiet=True)
        args, checks = _parse_args(sys.argv[1:])
        args[STR.action] = args.get(STR.action, args[STR.mode])
        for check in checks[args[STR.mode]].get(args[STR.action], []):
            check(args)
        setup_logging(quiet=args.get(STR.quiet, False), verbose=args.get(STR.verbose, False))
    except UWError as e:
        _abort(str(e))
    try:
        log.debug("Command: %s %s", Path(sys.argv[0]).name, " ".join(sys.argv[1:]))
        tools: dict[str, Callable[..., bool]] = {
            STR.config: _dispatch_config,
            STR.execute: _dispatch_execute,
            STR.fs: _dispatch_fs,
            STR.rocoto: _dispatch_rocoto,
            STR.template: _dispatch_template,
        }
        drivers: dict[str, Callable[..., bool]] = {
            x: partial(_dispatch_to_driver, x)
            for x in [
                STR.cdeps,
                STR.chgrescube,
                STR.esggrid,
                STR.filtertopo,
                STR.fv3,
                STR.globalequivresol,
                STR.gsi,
                STR.ioda,
                STR.jedi,
                STR.makehgrid,
                STR.makesolomosaic,
                STR.mpas,
                STR.mpasinit,
                STR.mpassit,
                STR.orog,
                STR.oroggsl,
                STR.schism,
                STR.sfcclimogen,
                STR.shave,
                STR.ungrib,
                STR.upp,
                STR.upp_assets,
                STR.ww3,
            ]
        }
        modes = {**tools, **drivers}
        sys.exit(0 if modes[args[STR.mode]](args) else 1)
    except UWError as e:
        for line in str(e).split("\n"):
            log.error(line)
        sys.exit(1)


# Mode config


def _add_subparser_config(subparsers: Subparsers) -> ModeChecks:
    """
    Add subparser for mode: config.

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
    Add subparser for mode: config compare.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.compare, "Compare configs")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_file_path(required, switch=_switch(STR.path1), helpmsg="Path to file 1")
    _add_arg_file_path(required, switch=_switch(STR.path2), helpmsg="Path to file 2")
    optional = _basic_setup(parser)
    _add_arg_file_format(
        optional,
        switch=_switch(STR.fmt1),
        helpmsg="Format of file 1",
        choices=FORMATS,
    )
    _add_arg_file_format(
        optional,
        switch=_switch(STR.fmt2),
        helpmsg="Format of file 2",
        choices=FORMATS,
    )
    return [
        *_add_args_verbosity(optional),
        partial(_check_file_vs_format, STR.path1, STR.fmt1),
        partial(_check_file_vs_format, STR.path2, STR.fmt2),
    ]


def _add_subparser_config_realize(subparsers: Subparsers) -> ActionChecks:
    """
    Add subparser for mode: config realize.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.realize, "Realize config")
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    _add_arg_input_format(optional, choices=FORMATS)
    _add_arg_update_file(optional)
    _add_arg_update_format(optional, choices=FORMATS)
    _add_arg_output_file(optional)
    _add_arg_output_format(optional, choices=FORMATS)
    _add_arg_key_path(optional, helpmsg="Dot-separated path of keys to the block to be output")
    _add_arg_values_needed(optional, helpmsg="Print report of values needed to realize config")
    _add_arg_total(optional)
    _add_arg_dry_run(optional)
    return [
        *_add_args_verbosity(optional),
        partial(_check_file_vs_format, STR.infile, STR.infmt),
        partial(_check_file_vs_format, STR.outfile, STR.outfmt),
        _check_update,
    ]


def _add_subparser_config_validate(subparsers: Subparsers) -> ActionChecks:
    """
    Add subparser for mode: config validate.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.validate, "Validate config")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_schema_file(required, required=True)
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    return _add_args_verbosity(optional)


def _dispatch_config(args: Args) -> bool:
    """
    Define dispatch logic for config mode.

    :param args: Parsed command-line args.
    """
    actions = {
        STR.compare: _dispatch_config_compare,
        STR.realize: _dispatch_config_realize,
        STR.validate: _dispatch_config_validate,
    }
    return actions[args[STR.action]](args)


def _dispatch_config_compare(args: Args) -> bool:
    """
    Define dispatch logic for config compare action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.config.compare(
        path1=args[STR.path1],
        format1=args[STR.fmt1],
        path2=args[STR.path2],
        format2=args[STR.fmt2],
    )


def _dispatch_config_realize(args: Args) -> bool:
    """
    Define dispatch logic for config realize action.

    :param args: Parsed command-line args.
    """
    try:
        uwtools.api.config.realize(
            input_config=args[STR.infile],
            input_format=args[STR.infmt],
            update_config=args[STR.updatefile],
            update_format=args[STR.updatefmt],
            output_file=args[STR.outfile],
            output_format=args[STR.outfmt],
            key_path=args[STR.keypath],
            values_needed=args[STR.valsneeded],
            total=args[STR.total],
            dry_run=args[STR.dryrun],
            stdin_ok=True,
        )
    except UWConfigRealizeError:
        msg = "Config could not be realized. Try with %s for details."
        log.error(msg, _switch(STR.valsneeded))
        return False
    return True


def _dispatch_config_validate(args: Args) -> bool:
    """
    Define dispatch logic for config validate action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.config.validate(
        schema_file=args[STR.schemafile],
        config_path=args[STR.infile],
        stdin_ok=True,
    )


# Mode execute


def _add_subparser_execute(subparsers: Subparsers) -> ModeChecks:
    """
    Add subparser for mode: execute.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.execute, "Execute external driver.")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_module(required)
    _add_arg_classname(required)
    _add_arg_task(required)
    optional = _basic_setup(parser)
    _add_arg_config_file(optional)
    _add_arg_schema_file(optional)
    _add_arg_cycle(optional)
    _add_arg_leadtime(optional)
    _add_arg_batch(optional)
    _add_arg_dry_run(optional)
    _add_arg_graph_file(optional)
    _add_arg_key_path(optional, helpmsg="Dot-separated path of keys to driver config block")
    return {STR.execute: _add_args_verbosity(optional)}


def _dispatch_execute(args: Args) -> bool:
    """
    Define dispatch logic for execute mode.

    :param args: Parsed command-line args.
    """
    assets = uwtools.api.execute.execute(
        classname=args[STR.classname],
        module=args[STR.module],
        task=args[STR.task],
        schema_file=args[STR.schemafile],
        key_path=args[STR.keypath],
        dry_run=args[STR.dryrun],
        config=args[STR.cfgfile],
        graph_file=args[STR.graphfile],
        cycle=args[STR.cycle],
        leadtime=args[STR.leadtime],
        batch=args[STR.batch],
        stdin_ok=True,
    )
    return bool(assets)


# Mode fs


def _add_subparser_fs(subparsers: Subparsers) -> ModeChecks:
    """
    Add subparser for mode: fs.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.fs, "Handle filesystem items (files and directories)")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.action.upper())
    return {
        STR.copy: _add_subparser_fs_copy(subparsers),
        STR.hardlink: _add_subparser_fs_hardlink(subparsers),
        STR.link: _add_subparser_fs_link(subparsers),
        STR.makedirs: _add_subparser_fs_makedirs(subparsers),
    }


def _add_subparser_fs_common(parser: Parser) -> tuple[ActionChecks, Group]:
    """
    Perform common subparser setup for mode: fs {copy link makedirs}.

    :param parser: The parser to configure.
    """
    optional = _basic_setup(parser)
    _add_arg_config_file(optional)
    _add_arg_target_dir(optional, helpmsg="Root directory for relative destination paths")
    _add_arg_cycle(optional)
    _add_arg_leadtime(optional)
    _add_arg_dry_run(optional)
    _add_arg_key_path(optional, helpmsg="Dot-separated path of keys to config block to use")
    _add_arg_report(optional)
    return _add_args_verbosity(optional), optional


def _add_subparser_fs_copy(subparsers: Subparsers) -> ActionChecks:
    """
    Add subparser for mode: fs copy.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.copy, "Copy files")
    checks, _ = _add_subparser_fs_common(parser)
    return checks


def _add_subparser_fs_hardlink(subparsers: Subparsers) -> ActionChecks:
    """
    Add subparser for mode: fs hardlink.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.hardlink, "Create hardlinks")
    checks, optional = _add_subparser_fs_common(parser)
    _add_arg_symlink_fallback(optional)
    return checks


def _add_subparser_fs_link(subparsers: Subparsers) -> ActionChecks:
    """
    Add subparser for mode: fs link.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.link, "Create symlinks")
    checks, _ = _add_subparser_fs_common(parser)
    return checks


def _add_subparser_fs_makedirs(subparsers: Subparsers) -> ActionChecks:
    """
    Add subparser for mode: fs makedirs.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.makedirs, "Make directories")
    checks, _ = _add_subparser_fs_common(parser)
    return checks


def _dispatch_fs(args: Args) -> bool:
    """
    Define dispatch logic for fs mode.

    :param args: Parsed command-line args.
    """
    actions = {
        STR.copy: _dispatch_fs_copy,
        STR.hardlink: _dispatch_fs_hardlink,
        STR.link: _dispatch_fs_link,
        STR.makedirs: _dispatch_fs_makedirs,
    }
    return actions[args[STR.action]](args)


def _dispatch_fs_copy(args: Args) -> bool:
    """
    Define dispatch logic for fs copy action.

    :param args: Parsed command-line args.
    """
    report = uwtools.api.fs.copy(
        target_dir=args[STR.targetdir],
        config=args[STR.cfgfile],
        cycle=args[STR.cycle],
        leadtime=args[STR.leadtime],
        key_path=args[STR.keypath],
        dry_run=args[STR.dryrun],
        stdin_ok=True,
    )
    return _dispatch_fs_report(report=report if args[STR.report] else None)


def _dispatch_fs_hardlink(args: Args) -> bool:
    """
    Define dispatch logic for fs hardlink action.

    :param args: Parsed command-line args.
    """
    report = uwtools.api.fs.link(
        target_dir=args[STR.targetdir],
        config=args[STR.cfgfile],
        cycle=args[STR.cycle],
        hardlink=True,
        leadtime=args[STR.leadtime],
        key_path=args[STR.keypath],
        dry_run=args[STR.dryrun],
        stdin_ok=True,
        symlink_fallback=args[STR.symlinkfallback],
    )
    return _dispatch_fs_report(report=report if args[STR.report] else None)


def _dispatch_fs_link(args: Args) -> bool:
    """
    Define dispatch logic for fs link action.

    :param args: Parsed command-line args.
    """
    report = uwtools.api.fs.link(
        target_dir=args[STR.targetdir],
        config=args[STR.cfgfile],
        cycle=args[STR.cycle],
        leadtime=args[STR.leadtime],
        key_path=args[STR.keypath],
        dry_run=args[STR.dryrun],
        stdin_ok=True,
    )
    return _dispatch_fs_report(report=report if args[STR.report] else None)


def _dispatch_fs_makedirs(args: Args) -> bool:
    """
    Define dispatch logic for fs makedirs action.

    :param args: Parsed command-line args.
    """
    report = uwtools.api.fs.makedirs(
        target_dir=args[STR.targetdir],
        config=args[STR.cfgfile],
        cycle=args[STR.cycle],
        leadtime=args[STR.leadtime],
        key_path=args[STR.keypath],
        dry_run=args[STR.dryrun],
        stdin_ok=True,
    )
    return _dispatch_fs_report(report=report if args[STR.report] else None)


def _dispatch_fs_report(report: dict[str, list[str]] | None) -> bool:
    if report:
        print(json.dumps(report, indent=2, sort_keys=True))
    return True


# Mode rocoto


def _add_subparser_rocoto(subparsers: Subparsers) -> ModeChecks:
    """
    Add subparser for mode: rocoto.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.rocoto, "Realize and validate Rocoto XML documents")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.action.upper())
    return {
        STR.iterate: _add_subparser_rocoto_iterate(subparsers),
        STR.realize: _add_subparser_rocoto_realize(subparsers),
        STR.validate: _add_subparser_rocoto_validate(subparsers),
    }


def _add_subparser_rocoto_iterate(subparsers: Subparsers) -> ActionChecks:
    """
    Add subparser for mode: rocoto iterate.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.iterate, "Iterate a Rocoto workflow")
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_cycle(required)
    _add_arg_database(required)
    _add_arg_task(required)
    _add_arg_workflow(required)
    optional = _basic_setup(parser)
    _add_arg_rate(optional)
    return _add_args_verbosity(optional)


def _add_subparser_rocoto_realize(subparsers: Subparsers) -> ActionChecks:
    """
    Add subparser for mode: rocoto realize.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.realize, "Realize a Rocoto XML workflow document")
    optional = _basic_setup(parser)
    _add_arg_config_file(optional)
    _add_arg_output_file(optional)
    return _add_args_verbosity(optional)


def _add_subparser_rocoto_validate(subparsers: Subparsers) -> ActionChecks:
    """
    Add subparser for mode: rocoto validate.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.validate, "Validate Rocoto XML")
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    return _add_args_verbosity(optional)


def _dispatch_rocoto(args: Args) -> bool:
    """
    Define dispatch logic for rocoto mode.

    :param args: Parsed command-line args.
    """
    actions = {
        STR.iterate: _dispatch_rocoto_iterate,
        STR.realize: _dispatch_rocoto_realize,
        STR.validate: _dispatch_rocoto_validate,
    }
    return actions[args[STR.action]](args)


def _dispatch_rocoto_iterate(args: Args) -> bool:
    """
    Define dispatch logic for rocoto iterate action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.rocoto.iterate(
        cycle=args[STR.cycle],
        database=args[STR.database],
        rate=args[STR.rate],
        task=args[STR.task],
        workflow=args[STR.workflow],
    )


def _dispatch_rocoto_realize(args: Args) -> bool:
    """
    Define dispatch logic for rocoto realize action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.rocoto.realize(
        config=args[STR.cfgfile],
        output_file=args[STR.outfile],
        stdin_ok=True,
    )


def _dispatch_rocoto_validate(args: Args) -> bool:
    """
    Define dispatch logic for rocoto validate action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.rocoto.validate(xml_file=args[STR.infile], stdin_ok=True)


# Mode template


def _add_subparser_template(subparsers: Subparsers) -> ModeChecks:
    """
    Add subparser for mode: template.

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
    Add subparser for mode: template translate.

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
    Add subparser for mode: template render.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.render, "Render a template")
    optional = _basic_setup(parser)
    _add_arg_input_file(optional)
    _add_arg_output_file(optional)
    _add_arg_values_file(optional)
    _add_arg_values_format(optional, choices=FORMATS)
    _add_arg_env(optional)
    _add_arg_search_path(optional)
    _add_arg_values_needed(optional, helpmsg="Print report of values needed to render template")
    _add_arg_dry_run(optional)
    checks = _add_args_verbosity(optional)
    _add_arg_key_eq_val_pairs(optional)
    return [*checks, _check_template_render_vals_args]


def _dispatch_template(args: Args) -> bool:
    """
    Define dispatch logic for template mode.

    :param args: Parsed command-line args.
    """
    actions = {
        STR.render: _dispatch_template_render,
        STR.translate: _dispatch_template_translate,
    }
    return actions[args[STR.action]](args)


def _dispatch_template_render(args: Args) -> bool:
    """
    Define dispatch logic for template render action.

    :param args: Parsed command-line args.
    """
    try:
        uwtools.api.template.render(
            values_src=args[STR.valsfile],
            values_format=args[STR.valsfmt],
            input_file=args[STR.infile],
            output_file=args[STR.outfile],
            overrides=_dict_from_key_eq_val_strings(args[STR.keyvalpairs]),
            env=args[STR.env],
            searchpath=args[STR.searchpath],
            values_needed=args[STR.valsneeded],
            dry_run=args[STR.dryrun],
            stdin_ok=True,
        )
    except UWTemplateRenderError:
        if args[STR.valsneeded]:
            return True
        log.error("Template could not be rendered")
        return False
    return True


def _dispatch_template_translate(args: Args) -> bool:
    """
    Define dispatch logic for template translate action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.template.translate(
        input_file=args[STR.infile],
        output_file=args[STR.outfile],
        dry_run=args[STR.dryrun],
        stdin_ok=True,
    )


# Arguments


def _add_arg_batch(group: Group) -> None:
    group.add_argument(
        _switch(STR.batch),
        action="store_true",
        help="Submit job to batch scheduler",
    )


def _add_arg_classname(group: Group) -> None:
    group.add_argument(
        _switch(STR.classname),
        help="Name of driver class",
        required=True,
        type=str,
    )


def _add_arg_config_file(group: Group, required: bool = False) -> None:
    msg = "Path to UW YAML config file" + ("" if required else " (default: read from stdin)")
    group.add_argument(
        _switch(STR.cfgfile),
        "-c",
        help=msg,
        metavar="PATH",
        required=required,
        type=Path,
    )


def _add_arg_cycle(group: Group, required: bool = False) -> None:
    group.add_argument(
        _switch(STR.cycle),
        help="The cycle in ISO8601 format (e.g. yyyy-mm-ddThh)",
        required=required,
        type=dt.datetime.fromisoformat,
    )


def _add_arg_database(group: Group) -> None:
    group.add_argument(
        _switch(STR.database),
        "-d",
        help="The Rocoto database file",
        required=True,
        type=Path,
    )


def _add_arg_dry_run(group: Group) -> None:
    group.add_argument(
        _switch(STR.dryrun),
        action="store_true",
        help="Only log info, making no changes",
    )


def _add_arg_env(group: Group) -> None:
    group.add_argument(
        _switch(STR.env),
        action="store_true",
        help="Use environment variables",
    )


def _add_arg_file_format(
    group: Group, switch: str, helpmsg: str, choices: list[str], required: bool = False
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


def _add_arg_graph_file(group: Group) -> None:
    group.add_argument(
        _switch(STR.graphfile),
        help="Path to Graphviz DOT output [experimental]",
        metavar="PATH",
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


def _add_arg_input_format(group: Group, choices: list[str], required: bool = False) -> None:
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


def _add_arg_key_path(group: Group, helpmsg: str) -> None:
    group.add_argument(
        _switch(STR.keypath),
        help=helpmsg,
        metavar="KEY[.KEY...]",
        required=False,
        type=lambda s: s.split("."),
    )


def _add_arg_leadtime(group: Group, required: bool = False) -> None:
    group.add_argument(
        _switch(STR.leadtime),
        help=f"The leadtime as {LEADTIME_DESC}",
        required=required,
        type=_timedelta_from_str,
    )


def _add_arg_module(group: Group) -> None:
    group.add_argument(
        _switch(STR.module),
        help="Path to driver module or name of module on sys.path",
        required=True,
        type=str,
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


def _add_arg_output_format(group: Group, choices: list[str], required: bool = False) -> None:
    group.add_argument(
        _switch(STR.outfmt),
        choices=choices,
        help="Output format",
        required=required,
        type=str,
    )


def _add_arg_quiet(group: Group) -> None:
    group.add_argument(
        _switch(STR.quiet),
        "-q",
        action="store_true",
        help="Print no logging messages",
    )


def _add_arg_rate(group: Group) -> None:
    default_rate = uwtools.rocoto.DEFAULT_ITERATION_RATE
    group.add_argument(
        _switch(STR.rate),
        "-r",
        default=default_rate,
        help="Delay between workflow iterations (default: %s)" % default_rate,
        metavar="SECONDS",
        required=False,
        type=int,
    )


def _add_arg_report(group: Group) -> None:
    group.add_argument(
        _switch(STR.report),
        action="store_true",
        help="Show JSON report on [non]ready assets",
    )


def _add_arg_symlink_fallback(group: Group) -> None:
    group.add_argument(
        _switch(STR.symlinkfallback),
        action="store_true",
        help="Symlink if hardlink fails",
    )


def _add_arg_schema_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        _switch(STR.schemafile),
        help="Path to schema file to use for validation",
        metavar="PATH",
        required=required,
        type=Path,
    )


def _add_arg_search_path(group: Group) -> None:
    group.add_argument(
        _switch(STR.searchpath),
        help="Colon-separated paths to search for extra templates",
        metavar="PATH[:PATH:...]",
        required=False,
        type=lambda s: s.split(":"),
    )


def _add_arg_show_schema(group: Group) -> None:
    group.add_argument(
        _switch(STR.showschema),
        action="store_true",
        help="Show driver schema and exit",
    )


def _add_arg_target_dir(group: Group, required: bool = False, helpmsg: str | None = None) -> None:
    group.add_argument(
        _switch(STR.targetdir),
        help=helpmsg or "Path to target directory",
        metavar="PATH",
        required=required,
        type=Path,
    )


def _add_arg_task(group: Group) -> None:
    group.add_argument(
        _switch(STR.task),
        help="Task to execute",
        required=True,
        type=str,
    )


def _add_arg_total(group: Group) -> None:
    group.add_argument(
        _switch(STR.total),
        action="store_true",
        help="Require rendering of all Jinja2 variables/expressions",
    )


def _add_arg_update_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        _switch(STR.updatefile),
        "-u",
        help="Path to update file (defaults to stdin)",
        metavar="PATH",
        required=required,
        type=Path,
    )


def _add_arg_update_format(group: Group, choices: list[str], required: bool = False) -> None:
    group.add_argument(
        _switch(STR.updatefmt),
        choices=choices,
        help="Update format",
        required=required,
        type=str,
    )


def _add_arg_values_file(group: Group, required: bool = False) -> None:
    group.add_argument(
        _switch(STR.valsfile),
        help="Path to file providing override or interpolation values",
        metavar="PATH",
        required=required,
        type=Path,
    )


def _add_arg_values_format(group: Group, choices: list[str]) -> None:
    group.add_argument(
        _switch(STR.valsfmt),
        choices=choices,
        help="Values format",
        required=False,
        type=str,
    )


def _add_arg_values_needed(group: Group, helpmsg: str) -> None:
    group.add_argument(
        _switch(STR.valsneeded),
        action="store_true",
        help=helpmsg,
    )


def _add_arg_verbose(group: Group) -> None:
    group.add_argument(
        _switch(STR.verbose),
        "-v",
        action="store_true",
        help="Print all logging messages",
    )


def _add_arg_workflow(group: Group) -> None:
    group.add_argument(
        _switch(STR.workflow),
        "-w",
        help="The Rocoto XML file",
        required=True,
        type=Path,
    )


# Support


def _abort(msg: str) -> NoReturn:
    """
    Exit with an informative message and error status.

    :param msg: The message to print.
    """
    print(msg, file=sys.stderr)
    sys.exit(1)


def _add_args_verbosity(group: Group) -> ActionChecks:
    """
    Add quiet and verbose arguments.

    :param group: The group to add the arguments to.
    :return: Check for mutual exclusivity of quiet/verbose arguments.
    """
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


def _add_subparser_for_driver(
    name: str,
    subparsers: Subparsers,
    with_batch: bool | None = False,
    with_cycle: bool | None = False,
    with_leadtime: bool | None = False,
) -> ModeChecks:
    """
    Add subparser for a standalone-driver mode.

    :param name: Name of the driver whose subparser to configure.
    :param subparsers: Parent parser's subparsers, to add this subparser to.
    :param with_batch: Does this driver accept a batch argument?
    :param with_cycle: Does this driver require a cycle?
    :param with_leadtime: Does this driver require a leadtime?
    """
    parser = _add_subparser(subparsers, name, "Execute %s tasks" % name)
    optional = _basic_setup(parser)
    _add_arg_show_schema(optional)
    subparsers = _add_subparsers(parser, STR.action, STR.task.upper(), required=False)
    return {
        task: _add_subparser_for_driver_task(
            subparsers, task, helpmsg, with_batch, with_cycle, with_leadtime
        )
        for task, helpmsg in import_module("uwtools.api.%s" % name).tasks().items()
    }


def _add_subparser_for_driver_task(
    subparsers: Subparsers,
    task: str,
    helpmsg: str,
    with_batch: bool | None = False,
    with_cycle: bool | None = False,
    with_leadtime: bool | None = False,
) -> ActionChecks:
    """
    Add subparser for a driver action.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    :param task: The task to add a subparser for.
    :param helpmsg: Help message for task.
    :param with_batch: Does this driver accept a batch argument?
    :param with_cycle: Does this driver require a cycle?
    :param with_leadtime: Does this driver require a leadtime?
    """
    parser = _add_subparser(subparsers, task, helpmsg.rstrip("."))
    required = parser.add_argument_group(TITLE_REQ_ARG)
    if with_cycle:
        _add_arg_cycle(required, required=True)
    if with_leadtime:
        _add_arg_leadtime(required, required=True)
    optional = _basic_setup(parser)
    _add_arg_config_file(optional)
    if with_batch:
        _add_arg_batch(optional)
    _add_arg_dry_run(optional)
    _add_arg_graph_file(optional)
    _add_arg_key_path(
        optional,
        helpmsg="Dot-separated path of keys to driver config block",
    )
    _add_arg_schema_file(optional)
    return _add_args_verbosity(optional)


def _add_subparsers(parser: Parser, dest: str, metavar: str, required: bool = True) -> Subparsers:
    """
    Add subparsers to a parser.

    :param parser: The parser to add subparsers to.
    :param dest: Name of parser attribute to store subparser under.
    :param metavar: Name for hierarchy of subparsers as shown by --help.
    :return: The new subparsers object.
    """
    return parser.add_subparsers(
        dest=dest, metavar=metavar, required=required, title="Positional arguments"
    )


def _basic_setup(parser: Parser) -> Group:
    """
    Create optional-arguments group and add help switch.

    :param parser: The parser to add the optional group to.
    """
    optional = parser.add_argument_group("Optional arguments")
    optional.add_argument("-h", _switch(STR.help), action=STR.help, help="Show help and exit")
    optional.add_argument(
        _switch(STR.version),
        action=STR.version,
        help="Show version info and exit",
        version=f"{Path(sys.argv[0]).name} {_version()}",
    )
    return optional


def _check_file_vs_format(file_arg: str, format_arg: str, args: Args) -> Args:
    if args.get(format_arg) is None:
        args[format_arg] = get_config_format(args[file_arg])
    return args


def _check_template_render_vals_args(args: Args) -> Args:
    # In "template render" mode, a values file is optional, as values used to render the template
    # will be taken from the environment or from key=value command-line pairs by default. But if a
    # values file IS specified, its format must either be explicitly specified, or deduced from its
    # extension.
    if args.get(STR.valsfile) is not None and args.get(STR.valsfmt) is None:
        args[STR.valsfmt] = get_config_format(args[STR.valsfile])
    return args


def _check_update(args: Args) -> Args:
    if args.get(STR.updatefile) is not None and args.get(STR.updatefmt) is None:
        args[STR.updatefmt] = get_config_format(args[STR.updatefile])
    return args


def _check_verbosity(args: Args) -> Args:
    if args.get(STR.quiet) and args.get(STR.verbose):
        _abort("%s may not be used with %s" % (_switch(STR.quiet), _switch(STR.verbose)))
    return args


def _dict_from_key_eq_val_strings(config_items: list[str]) -> dict[str, str]:
    """
    Given a list of key=value strings, return a dictionary of key/value pairs.

    :param config_items: Strings in the form key=value.
    :return: A dictionary based on the input key=value strings.
    """
    return dict([arg.split("=") for arg in config_items])


def _dispatch_to_driver(name: str, args: Args) -> bool:
    """
    Define dispatch logic for a driver mode.

    :param name: Name of the driver to dispatch to.
    :param args: Parsed command-line args.
    """
    module = import_module("uwtools.api.%s" % name)
    if args.get(STR.showschema):
        print(json.dumps(module.schema(), sort_keys=True, indent=2))
        return True
    if not args.get(STR.action):
        _abort("No %s specified" % STR.task.upper())
    execute: Callable[..., bool] = module.execute
    kwargs = {
        "task": args[STR.action],
        "config": args[STR.cfgfile],
        "dry_run": args[STR.dryrun],
        "graph_file": args[STR.graphfile],
        "key_path": args[STR.keypath],
        "schema_file": args[STR.schemafile],
        "stdin_ok": True,
    }
    for k in [STR.batch, STR.cycle, STR.leadtime]:
        if k in args:
            kwargs[k] = args.get(k)
    return execute(**kwargs)


def _formatter(prog: str) -> HelpFormatter:
    """
    Return a standard formatter for help messages.
    """
    # max_help_positions sets the maximum starting column for option help text.
    return HelpFormatter(prog, max_help_position=6)


def _parse_args(raw_args: list[str]) -> tuple[Args, Checks]:
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
    tools = {
        STR.config: partial(_add_subparser_config, subparsers),
        STR.execute: partial(_add_subparser_execute, subparsers),
        STR.fs: partial(_add_subparser_fs, subparsers),
        STR.rocoto: partial(_add_subparser_rocoto, subparsers),
        STR.template: partial(_add_subparser_template, subparsers),
    }
    no_components: list[str] = []
    assets = {
        component: partial(_add_subparser_for_driver, component, subparsers)
        for component in no_components
    }
    assets_with_cycle = {
        component: partial(_add_subparser_for_driver, component, subparsers, with_cycle=True)
        for component in [
            STR.cdeps,
            STR.schism,
            STR.ww3,
        ]
    }
    assets_with_cycle_and_leadtime = {
        component: partial(
            _add_subparser_for_driver, component, subparsers, with_cycle=True, with_leadtime=True
        )
        for component in [STR.upp_assets]
    }
    drivers = {
        component: partial(_add_subparser_for_driver, component, subparsers, with_batch=True)
        for component in [
            STR.esggrid,
            STR.filtertopo,
            STR.globalequivresol,
            STR.makehgrid,
            STR.makesolomosaic,
            STR.orog,
            STR.oroggsl,
            STR.sfcclimogen,
            STR.shave,
        ]
    }
    drivers_with_cycle = {
        component: partial(
            _add_subparser_for_driver, component, subparsers, with_batch=True, with_cycle=True
        )
        for component in [
            STR.fv3,
            STR.gsi,
            STR.ioda,
            STR.jedi,
            STR.mpas,
            STR.mpasinit,
            STR.ungrib,
        ]
    }
    drivers_with_cycle_and_leadtime = {
        component: partial(
            _add_subparser_for_driver,
            component,
            subparsers,
            with_batch=True,
            with_cycle=True,
            with_leadtime=True,
        )
        for component in [
            STR.chgrescube,
            STR.mpassit,
            STR.upp,
        ]
    }
    modes = {
        **tools,
        **assets,
        **assets_with_cycle,
        **assets_with_cycle_and_leadtime,
        **drivers,
        **drivers_with_cycle,
        **drivers_with_cycle_and_leadtime,
    }
    checks = {k: modes[k]() for k in sorted(modes.keys())}
    return vars(parser.parse_args(raw_args)), checks


def _switch(arg: str) -> str:
    """
    Convert argument name to long-form switch.

    :param arg: Internal name of parsed argument.
    :return: The long-form switch.
    """
    return "--%s" % arg.replace("_", "-")


def _timedelta_from_str(tds: str) -> dt.timedelta:
    """
    Return a timedelta parsed from a leadtime string.

    :param tds: The timedelta string to parse.
    """
    if matches := re.match(r"(\d+)(:(\d+))?(:(\d+))?", tds):
        h, m, s = [int(matches.groups()[n] or 0) for n in (0, 2, 4)]
        return dt.timedelta(hours=h, minutes=m, seconds=s)
    _abort(f"Specify leadtime as {LEADTIME_DESC}")


def _version() -> str:
    """
    Return version information.
    """
    info = json.loads(resource_path("info.json").read_text())
    return "version %s build %s" % (info["version"], info["buildnum"])
