"""
Modal CLI.
"""

import datetime as dt
import json
import sys
from argparse import ArgumentParser as Parser
from argparse import HelpFormatter
from argparse import _ArgumentGroup as Group
from argparse import _SubParsersAction as Subparsers
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, List, NoReturn, Tuple

import uwtools.api
import uwtools.api.chgres_cube
import uwtools.api.config
import uwtools.api.esg_grid
import uwtools.api.file
import uwtools.api.fv3
import uwtools.api.jedi
import uwtools.api.mpas
import uwtools.api.mpas_init
import uwtools.api.rocoto
import uwtools.api.sfc_climo_gen
import uwtools.api.template
import uwtools.api.ungrib
import uwtools.config.jinja2
import uwtools.rocoto
from uwtools.exceptions import UWConfigRealizeError, UWError, UWTemplateRenderError
from uwtools.logging import log, setup_logging
from uwtools.strings import FORMAT, STR
from uwtools.utils.file import get_file_format, resource_path

FORMATS = FORMAT.extensions()
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

    try:
        setup_logging(quiet=True)
        args, checks = _parse_args(sys.argv[1:])
        for check in checks[args[STR.mode]][args[STR.action]]:
            check(args)
        setup_logging(quiet=args[STR.quiet], verbose=args[STR.verbose])
    except UWError as e:
        _abort(str(e))
    try:
        log.debug("Command: %s %s", Path(sys.argv[0]).name, " ".join(sys.argv[1:]))
        modes: Dict[str, Callable[..., bool]] = {
            STR.chgrescube: partial(_dispatch_to_driver, "chgres_cube"),
            STR.config: _dispatch_config,
            STR.esggrid: _dispatch_esg_grid,
            STR.file: _dispatch_file,
            STR.fv3: _dispatch_fv3,
            STR.jedi: _dispatch_jedi,
            STR.mpas: _dispatch_mpas,
            STR.mpasinit: _dispatch_mpas_init,
            STR.rocoto: _dispatch_rocoto,
            STR.sfcclimogen: _dispatch_sfc_climo_gen,
            STR.template: _dispatch_template,
            STR.ungrib: _dispatch_ungrib,
        }
        sys.exit(0 if modes[args[STR.mode]](args) else 1)
    except UWError as e:
        log.error(str(e))
        sys.exit(1)


# PM


def _add_subparser_for_driver(name: str, subparsers: Subparsers) -> ModeChecks:
    """
    Subparser for a driver mode.

    :param name: Name of the driver whose subparser to configure.
    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.chgrescube, "Execute %s tasks" % name)
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.task.upper())
    return {
        task: _add_subparser_for_driver_task(subparsers, task, helpmsg)
        for task, helpmsg in getattr(uwtools.api, name).tasks().items()
    }


def _add_subparser_for_driver_task(subparsers: Subparsers, task: str, helpmsg: str) -> ActionChecks:
    """
    Subparser for a driver action.

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    :param task: The task to add a subparser for.
    :param helpmsg: Help message for task.
    """
    parser = _add_subparser(subparsers, task, helpmsg.rstrip("."))
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_cycle(required)
    optional = _basic_setup(parser)
    _add_arg_config_file(group=optional)
    _add_arg_batch(optional)
    _add_arg_dry_run(optional)
    _add_arg_graph_file(optional)
    checks = _add_args_verbosity(optional)
    return checks


def _dispatch_to_driver(name: str, args: Args) -> bool:
    """
    Dispatch logic for a driver mode.

    :param name: Name of the driver to dispatch to.
    :param args: Parsed command-line args.
    """
    execute: Callable[..., bool] = getattr(uwtools.api, name).execute
    return execute(
        task=args[STR.action],
        config=args[STR.cfgfile],
        cycle=args[STR.cycle],
        batch=args[STR.batch],
        dry_run=args[STR.dryrun],
        graph_file=args[STR.graphfile],
        stdin_ok=True,
    )


# PM

# Mode chgres_cube


def _add_subparser_chgres_cube(subparsers: Subparsers) -> ModeChecks:
    """
    Subparser for mode: chgres_cube

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.chgrescube, "Execute chgres_cube tasks")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.task.upper())
    return {
        task: _add_subparser_chgres_cube_task(subparsers, task, helpmsg)
        for task, helpmsg in uwtools.api.chgres_cube.tasks().items()
    }


def _add_subparser_chgres_cube_task(
    subparsers: Subparsers, task: str, helpmsg: str
) -> ActionChecks:
    """
    Subparser for mode: chgres_cube <task>

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    :param task: The task to add a subparser for.
    :param helpmsg: Help message for task.
    """
    parser = _add_subparser(subparsers, task, helpmsg.rstrip("."))
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_cycle(required)
    optional = _basic_setup(parser)
    _add_arg_config_file(group=optional)
    _add_arg_batch(optional)
    _add_arg_dry_run(optional)
    _add_arg_graph_file(optional)
    checks = _add_args_verbosity(optional)
    return checks


def _dispatch_chgres_cube(args: Args) -> bool:
    """
    Dispatch logic for chgres_cube mode.

    :param args: Parsed command-line args.
    """
    return uwtools.api.chgres_cube.execute(
        task=args[STR.action],
        config=args[STR.cfgfile],
        cycle=args[STR.cycle],
        batch=args[STR.batch],
        dry_run=args[STR.dryrun],
        graph_file=args[STR.graphfile],
        stdin_ok=True,
    )


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
    _add_arg_output_block(optional)
    _add_arg_values_needed(optional)
    _add_arg_total(optional)
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
    actions = {
        STR.compare: _dispatch_config_compare,
        STR.realize: _dispatch_config_realize,
        STR.validate: _dispatch_config_validate,
    }
    return actions[args[STR.action]](args)


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
    try:
        uwtools.api.config.realize(
            input_config=args[STR.infile],
            input_format=args[STR.infmt],
            output_block=args[STR.outblock],
            output_file=args[STR.outfile],
            output_format=args[STR.outfmt],
            supplemental_configs=args[STR.suppfiles],
            values_needed=args[STR.valsneeded],
            total=args[STR.total],
            dry_run=args[STR.dryrun],
            stdin_ok=True,
        )
    except UWConfigRealizeError:
        log.error(
            "Config could not be realized. Try with %s for details." % _switch(STR.valsneeded)
        )
        return False
    return True


def _dispatch_config_validate(args: Args) -> bool:
    """
    Dispatch logic for config validate action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.config.validate(
        schema_file=args[STR.schemafile],
        config=args[STR.infile],
        stdin_ok=True,
    )


# Mode esg_grid


def _add_subparser_esg_grid(subparsers: Subparsers) -> ModeChecks:
    """
    Subparser for mode: esg_grid
    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.esggrid, "Execute esg_grid tasks")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.task.upper())
    return {
        task: _add_subparser_esg_grid_task(subparsers, task, helpmsg)
        for task, helpmsg in uwtools.api.esg_grid.tasks().items()
    }


def _add_subparser_esg_grid_task(subparsers: Subparsers, task: str, helpmsg: str) -> ActionChecks:
    """
    Subparser for mode: esg_grid <task>
    :param subparsers: Parent parser's subparsers, to add this subparser to.
    :param task: The task to add a subparser for.
    :param helpmsg: Help message for task.
    """
    parser = _add_subparser(subparsers, task, helpmsg.rstrip("."))
    optional = _basic_setup(parser)
    _add_arg_config_file(group=optional, required=False)
    _add_arg_batch(optional)
    _add_arg_dry_run(optional)
    _add_arg_graph_file(optional)
    checks = _add_args_verbosity(optional)
    return checks


def _dispatch_esg_grid(args: Args) -> bool:
    """
    Dispatch logic for esg_grid mode.

    :param args: Parsed command-line args.
    """
    return uwtools.api.esg_grid.execute(
        task=args[STR.action],
        config=args[STR.cfgfile],
        batch=args[STR.batch],
        dry_run=args[STR.dryrun],
        graph_file=args[STR.graphfile],
        stdin_ok=True,
    )


# Mode file


def _add_subparser_file(subparsers: Subparsers) -> ModeChecks:
    """
    Subparser for mode: file

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.file, "Handle files")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.action.upper())
    return {
        STR.copy: _add_subparser_file_copy(subparsers),
        STR.link: _add_subparser_file_link(subparsers),
    }


def _add_subparser_file_common(parser: Parser) -> ActionChecks:
    """
    Common subparser code for mode: file {copy link}

    :param parser: The parser to configure.
    """
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_target_dir(required, required=True)
    optional = _basic_setup(parser)
    _add_arg_config_file(group=optional)
    _add_arg_dry_run(optional)
    checks = _add_args_verbosity(optional)
    _add_arg_keys(optional)
    return checks


def _add_subparser_file_copy(subparsers: Subparsers) -> ActionChecks:
    """
    Subparser for mode: file copy

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.copy, "Copy files")
    return _add_subparser_file_common(parser)


def _add_subparser_file_link(subparsers: Subparsers) -> ActionChecks:
    """
    Subparser for mode: file link

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.link, "Link files")
    return _add_subparser_file_common(parser)


def _dispatch_file(args: Args) -> bool:
    """
    Dispatch logic for file mode.

    :param args: Parsed command-line args.
    """
    actions = {
        STR.copy: _dispatch_file_copy,
        STR.link: _dispatch_file_link,
    }
    return actions[args[STR.action]](args)


def _dispatch_file_copy(args: Args) -> bool:
    """
    Dispatch logic for file copy action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.file.copy(
        target_dir=args[STR.targetdir],
        config=args[STR.cfgfile],
        keys=args[STR.keys],
        dry_run=args[STR.dryrun],
        stdin_ok=True,
    )


def _dispatch_file_link(args: Args) -> bool:
    """
    Dispatch logic for file link action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.file.link(
        target_dir=args[STR.targetdir],
        config=args[STR.cfgfile],
        keys=args[STR.keys],
        dry_run=args[STR.dryrun],
        stdin_ok=True,
    )


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
    _add_arg_cycle(required)
    optional = _basic_setup(parser)
    _add_arg_config_file(group=optional)
    _add_arg_batch(optional)
    _add_arg_dry_run(optional)
    _add_arg_graph_file(optional)
    checks = _add_args_verbosity(optional)
    return checks


def _dispatch_fv3(args: Args) -> bool:
    """
    Dispatch logic for fv3 mode.

    :param args: Parsed command-line args.
    """
    return uwtools.api.fv3.execute(
        task=args[STR.action],
        config=args[STR.cfgfile],
        cycle=args[STR.cycle],
        batch=args[STR.batch],
        dry_run=args[STR.dryrun],
        graph_file=args[STR.graphfile],
        stdin_ok=True,
    )


# Mode jedi


def _add_subparser_jedi(subparsers: Subparsers) -> ModeChecks:
    """
    Subparser for mode: jedi
    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.jedi, "Execute JEDI tasks")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.task.upper())
    return {
        task: _add_subparser_jedi_task(subparsers, task, helpmsg)
        for task, helpmsg in uwtools.api.jedi.tasks().items()
    }


def _add_subparser_jedi_task(subparsers: Subparsers, task: str, helpmsg: str) -> ActionChecks:
    """
    Subparser for mode: jedi <task>

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    :param task: The task to add a subparser for.
    :param helpmsg: Help message for task.
    """
    parser = _add_subparser(subparsers, task, helpmsg.rstrip("."))
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_cycle(required)
    optional = _basic_setup(parser)
    _add_arg_config_file(group=optional)
    _add_arg_batch(optional)
    _add_arg_dry_run(optional)
    _add_arg_graph_file(optional)
    checks = _add_args_verbosity(optional)
    return checks


def _dispatch_jedi(args: Args) -> bool:
    """
    Dispatch logic for jedi mode.

    :param args: Parsed command-line args.
    """
    return uwtools.api.jedi.execute(
        task=args[STR.action],
        config=args[STR.cfgfile],
        cycle=args[STR.cycle],
        batch=args[STR.batch],
        dry_run=args[STR.dryrun],
        graph_file=args[STR.graphfile],
        stdin_ok=True,
    )


# Mode mpas


def _add_subparser_mpas(subparsers: Subparsers) -> ModeChecks:
    """
    Subparser for mode: mpas

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.mpas, "Execute MPAS tasks")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.task.upper())
    return {
        task: _add_subparser_mpas_task(subparsers, task, helpmsg)
        for task, helpmsg in uwtools.api.mpas.tasks().items()
    }


def _add_subparser_mpas_task(subparsers: Subparsers, task: str, helpmsg: str) -> ActionChecks:
    """
    Subparser for mode: mpas <task>

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    :param task: The task to add a subparser for.
    :param helpmsg: Help message for task.
    """
    parser = _add_subparser(subparsers, task, helpmsg.rstrip("."))
    required = parser.add_argument_group(TITLE_REQ_ARG)

    _add_arg_cycle(required)
    optional = _basic_setup(parser)
    _add_arg_config_file(group=optional)
    _add_arg_batch(optional)
    _add_arg_dry_run(optional)
    _add_arg_graph_file(optional)
    checks = _add_args_verbosity(optional)
    return checks


def _dispatch_mpas(args: Args) -> bool:
    """
    Dispatch logic for mpas mode.

    :param args: Parsed command-line args.
    """
    return uwtools.api.mpas.execute(
        task=args[STR.action],
        config=args[STR.cfgfile],
        cycle=args[STR.cycle],
        batch=args[STR.batch],
        dry_run=args[STR.dryrun],
        graph_file=args[STR.graphfile],
        stdin_ok=True,
    )


# Mode mpas_init


def _add_subparser_mpas_init(subparsers: Subparsers) -> ModeChecks:
    """
    Subparser for mode: mpas_init

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.mpasinit, "Execute MPAS Init tasks")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.task.upper())
    return {
        task: _add_subparser_mpas_init_task(subparsers, task, helpmsg)
        for task, helpmsg in uwtools.api.mpas_init.tasks().items()
    }


def _add_subparser_mpas_init_task(subparsers: Subparsers, task: str, helpmsg: str) -> ActionChecks:
    """
    Subparser for mode: mpas_init <task>

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    :param task: The task to add a subparser for.
    :param helpmsg: Help message for task.
    """
    parser = _add_subparser(subparsers, task, helpmsg.rstrip("."))
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_cycle(required)
    optional = _basic_setup(parser)
    _add_arg_config_file(group=optional)
    _add_arg_batch(optional)
    _add_arg_dry_run(optional)
    _add_arg_graph_file(optional)
    checks = _add_args_verbosity(optional)
    return checks


def _dispatch_mpas_init(args: Args) -> bool:
    """
    Dispatch logic for mpas_init mode.

    :param args: Parsed command-line args.
    """
    return uwtools.api.mpas_init.execute(
        task=args[STR.action],
        config=args[STR.cfgfile],
        cycle=args[STR.cycle],
        batch=args[STR.batch],
        dry_run=args[STR.dryrun],
        graph_file=args[STR.graphfile],
        stdin_ok=True,
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
    actions = {
        STR.realize: _dispatch_rocoto_realize,
        STR.validate: _dispatch_rocoto_validate,
    }
    return actions[args[STR.action]](args)


def _dispatch_rocoto_realize(args: Args) -> bool:
    """
    Dispatch logic for rocoto realize action. Validate input and output.

    :param args: Parsed command-line args.
    """
    return uwtools.api.rocoto.realize(
        config=args[STR.infile],
        output_file=args[STR.outfile],
        stdin_ok=True,
    )


def _dispatch_rocoto_validate(args: Args) -> bool:
    """
    Dispatch logic for rocoto validate action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.rocoto.validate(xml_file=args[STR.infile], stdin_ok=True)


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
    optional = _basic_setup(parser)
    _add_arg_config_file(group=optional)
    _add_arg_batch(optional)
    _add_arg_dry_run(optional)
    _add_arg_graph_file(optional)
    checks = _add_args_verbosity(optional)
    return checks


def _dispatch_sfc_climo_gen(args: Args) -> bool:
    """
    Dispatch logic for sfc_climo_gen mode.

    :param args: Parsed command-line args.
    """
    return uwtools.api.sfc_climo_gen.execute(
        task=args[STR.action],
        config=args[STR.cfgfile],
        batch=args[STR.batch],
        dry_run=args[STR.dryrun],
        graph_file=args[STR.graphfile],
        stdin_ok=True,
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
    _add_arg_env(optional)
    _add_arg_search_path(optional)
    _add_arg_values_needed(optional)
    _add_arg_dry_run(optional)
    checks = _add_args_verbosity(optional)
    _add_arg_key_eq_val_pairs(optional)
    return checks + [_check_template_render_vals_args]


def _dispatch_template(args: Args) -> bool:
    """
    Dispatch logic for template mode.

    :param args: Parsed command-line args.
    """
    actions = {
        STR.render: _dispatch_template_render,
        STR.translate: _dispatch_template_translate,
    }
    return actions[args[STR.action]](args)


def _dispatch_template_render(args: Args) -> bool:
    """
    Dispatch logic for template render action.

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
    Dispatch logic for template translate action.

    :param args: Parsed command-line args.
    """
    return uwtools.api.template.translate(
        input_file=args[STR.infile],
        output_file=args[STR.outfile],
        dry_run=args[STR.dryrun],
        stdin_ok=True,
    )


# Mode ungrib


def _add_subparser_ungrib(subparsers: Subparsers) -> ModeChecks:
    """
    Subparser for mode: ungrib

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    """
    parser = _add_subparser(subparsers, STR.ungrib, "Execute Ungrib tasks")
    _basic_setup(parser)
    subparsers = _add_subparsers(parser, STR.action, STR.task.upper())
    return {
        task: _add_subparser_ungrib_task(subparsers, task, helpmsg)
        for task, helpmsg in uwtools.api.ungrib.tasks().items()
    }


def _add_subparser_ungrib_task(subparsers: Subparsers, task: str, helpmsg: str) -> ActionChecks:
    """
    Subparser for mode: ungrib <task>

    :param subparsers: Parent parser's subparsers, to add this subparser to.
    :param task: The task to add a subparser for.
    :param helpmsg: Help message for task.
    """
    parser = _add_subparser(subparsers, task, helpmsg.rstrip("."))
    required = parser.add_argument_group(TITLE_REQ_ARG)
    _add_arg_cycle(required)
    optional = _basic_setup(parser)
    _add_arg_config_file(group=optional)
    _add_arg_batch(optional)
    _add_arg_dry_run(optional)
    _add_arg_graph_file(optional)
    checks = _add_args_verbosity(optional)
    return checks


def _dispatch_ungrib(args: Args) -> bool:
    """
    Dispatch logic for ungrib mode.

    :param args: Parsed command-line args.
    """
    return uwtools.api.ungrib.execute(
        task=args[STR.action],
        config=args[STR.cfgfile],
        cycle=args[STR.cycle],
        batch=args[STR.batch],
        dry_run=args[STR.dryrun],
        graph_file=args[STR.graphfile],
        stdin_ok=True,
    )


# Arguments

# pylint: disable=missing-function-docstring


def _add_arg_batch(group: Group) -> None:
    group.add_argument(
        _switch(STR.batch),
        action="store_true",
        help="Submit run to batch scheduler",
    )


def _add_arg_config_file(group: Group, required: bool = False) -> None:
    msg = "Path to config file" + ("" if required else " (default: read from stdin)")
    group.add_argument(
        _switch(STR.cfgfile),
        "-c",
        help=msg,
        metavar="PATH",
        required=required,
        type=Path,
    )


def _add_arg_cycle(group: Group) -> None:
    group.add_argument(
        _switch(STR.cycle),
        help="The cycle in ISO8601 format",
        required=True,
        type=dt.datetime.fromisoformat,
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


def _add_arg_keys(group: Group) -> None:
    group.add_argument(
        STR.keys,
        help="YAML key leading to file dst/src block",
        metavar="KEY",
        nargs="*",
    )


def _add_arg_output_block(group: Group):
    group.add_argument(
        _switch(STR.outblock),
        help="Dot-separated path of keys to the block to be output",
        metavar="KEY[.KEY[.KEY]...]",
        required=False,
        type=lambda s: s.split("."),
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


def _add_arg_search_path(group: Group) -> None:
    group.add_argument(
        _switch(STR.searchpath),
        help="Colon-separated paths to search for extra templates",
        metavar="PATH[:PATH:...]",
        required=False,
        type=lambda s: s.split(":"),
    )


def _add_arg_supplemental_files(group: Group) -> None:
    group.add_argument(
        STR.suppfiles,
        help="Additional files to supplement primary input",
        metavar="PATH",
        nargs="*",
        type=Path,
    )


def _add_arg_target_dir(group: Group, required: bool) -> None:
    group.add_argument(
        _switch(STR.targetdir),
        help="Path to target directory",
        metavar="PATH",
        required=required,
        type=Path,
    )


def _add_arg_total(group: Group) -> None:
    group.add_argument(
        _switch(STR.total),
        action="store_true",
        help="Require rendering of all Jinja2 variables/expressions",
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
    optional.add_argument(
        _switch(STR.version),
        action=STR.version,
        help="Show version info and exit",
        version=f"%(prog)s {_version()}",
    )
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
    if args.get(STR.quiet) and args.get(STR.verbose):
        _abort("%s may not be used with %s" % (_switch(STR.quiet), _switch(STR.verbose)))
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
        STR.chgrescube: _add_subparser_for_driver("chgres_cube", subparsers),
        STR.config: _add_subparser_config(subparsers),
        STR.esggrid: _add_subparser_esg_grid(subparsers),
        STR.file: _add_subparser_file(subparsers),
        STR.fv3: _add_subparser_fv3(subparsers),
        STR.jedi: _add_subparser_jedi(subparsers),
        STR.mpas: _add_subparser_mpas(subparsers),
        STR.mpasinit: _add_subparser_mpas_init(subparsers),
        STR.rocoto: _add_subparser_rocoto(subparsers),
        STR.sfcclimogen: _add_subparser_sfc_climo_gen(subparsers),
        STR.template: _add_subparser_template(subparsers),
        STR.ungrib: _add_subparser_ungrib(subparsers),
    }
    return vars(parser.parse_args(raw_args)), checks


def _switch(arg: str) -> str:
    """
    Convert argument name to long-form switch.

    :param arg: Internal name of parsed argument.
    :return: The long-form switch.
    """
    return "--%s" % arg.replace("_", "-")


def _version() -> str:
    """
    Return version information.
    """
    with open(resource_path("info.json"), "r", encoding="utf-8") as f:
        info = json.load(f)
        return "version %s build %s" % (info["version"], info["buildnum"])
