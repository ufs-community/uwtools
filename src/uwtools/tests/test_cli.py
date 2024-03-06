# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name
import datetime as dt
import logging
import sys
from argparse import ArgumentParser as Parser
from argparse import _SubParsersAction
from typing import List
from unittest.mock import patch

import pytest
from pytest import fixture, raises

import uwtools.api.config
import uwtools.api.fv3
import uwtools.api.mpas
import uwtools.api.rocoto
import uwtools.api.sfc_climo_gen
import uwtools.api.template
import uwtools.drivers.fv3
import uwtools.drivers.mpas
import uwtools.drivers.sfc_climo_gen
from uwtools import cli
from uwtools.cli import STR
from uwtools.exceptions import UWConfigRealizeError, UWError, UWTemplateRenderError
from uwtools.logging import log
from uwtools.tests.support import regex_logged
from uwtools.utils.file import FORMAT

# Test functions


def test__abort(capsys):
    msg = "Aborting..."
    with raises(SystemExit) as e:
        cli._abort(msg)
    assert e.value.code == 1
    assert msg in capsys.readouterr().err


def test__add_subparser_config(subparsers):
    cli._add_subparser_config(subparsers)
    assert actions(subparsers.choices[STR.config]) == [STR.compare, STR.realize, STR.validate]


def test__add_subparser_config_compare(subparsers):
    cli._add_subparser_config_compare(subparsers)
    assert subparsers.choices[STR.compare]


def test__add_subparser_config_realize(subparsers):
    cli._add_subparser_config_realize(subparsers)
    assert subparsers.choices[STR.realize]


def test__add_subparser_config_validate(subparsers):
    cli._add_subparser_config_validate(subparsers)
    assert subparsers.choices[STR.validate]


def test__add_subparser_fv3(subparsers):
    cli._add_subparser_fv3(subparsers)
    assert actions(subparsers.choices[STR.fv3]) == [
        "boundary_files",
        "diag_table",
        "field_table",
        "files_copied",
        "files_linked",
        "model_configure",
        "namelist_file",
        "provisioned_run_directory",
        "restart_directory",
        "run",
        "runscript",
    ]


def test__add_subparser_mpas(subparsers):
    cli._add_subparser_mpas(subparsers)
    assert actions(subparsers.choices[STR.mpas]) == [
        "boundary_files",
        "field_table",
        "files_copied",
        "files_linked",
        "model_configure",
        "namelist_file",
        "provisioned_run_directory",
        "restart_directory",
        "run",
        "runscript",
    ]


def test__add_subparser_rocoto(subparsers):
    cli._add_subparser_rocoto(subparsers)
    assert subparsers.choices[STR.rocoto]


def test__add_subparser_rocoto_realize(subparsers):
    cli._add_subparser_rocoto_realize(subparsers)
    assert subparsers.choices[STR.realize]


def test__add_subparser_rocoto_validate(subparsers):
    cli._add_subparser_rocoto_validate(subparsers)
    assert subparsers.choices[STR.validate]


def test__add_subparser_sfc_climo_gen(subparsers):
    cli._add_subparser_sfc_climo_gen(subparsers)
    assert actions(subparsers.choices[STR.sfcclimogen]) == [
        "namelist_file",
        "provisioned_run_directory",
        "run",
        "runscript",
    ]


def test__add_subparser_template(subparsers):
    cli._add_subparser_template(subparsers)
    assert actions(subparsers.choices[STR.template]) == [STR.render, STR.translate]


def test__add_subparser_template_render(subparsers):
    cli._add_subparser_template_render(subparsers)
    assert subparsers.choices[STR.render]


def test__add_subparser_template_translate(subparsers):
    cli._add_subparser_template_translate(subparsers)
    assert subparsers.choices[STR.translate]


@pytest.mark.parametrize(
    "vals",
    [
        (STR.file1path, STR.file1fmt),
        (STR.file2path, STR.file2fmt),
        (STR.infile, STR.infmt),
        (STR.outfile, STR.outfmt),
        (STR.valsfile, STR.valsfmt),
    ],
)
def test__check_file_vs_format_fail(capsys, vals):
    # When reading/writing from/to stdin/stdout, the data format must be specified, since there is
    # no filename to deduce it from.
    file_arg, format_arg = vals
    args = dict(file_arg=None, format_arg=None)
    with raises(SystemExit):
        cli._check_file_vs_format(file_arg=file_arg, format_arg=format_arg, args=args)
    assert (
        "Specify %s when %s is not specified" % (cli._switch(format_arg), cli._switch(file_arg))
        in capsys.readouterr().err
    )


def test__check_file_vs_format_pass_explicit():
    # Accept explicitly-specified format, whatever it is.
    fmt = "jpg"
    args = {STR.infile: "/path/to/input.txt", STR.infmt: fmt}
    args = cli._check_file_vs_format(
        file_arg=STR.infile,
        format_arg=STR.infmt,
        args=args,
    )
    assert args[STR.infmt] == fmt


@pytest.mark.parametrize("fmt", FORMAT.formats())
def test__check_file_vs_format_pass_implicit(fmt):
    # The format is correctly deduced for a file with a known extension.
    args = {STR.infile: f"/path/to/input.{fmt}", STR.infmt: None}
    args = cli._check_file_vs_format(
        file_arg=STR.infile,
        format_arg=STR.infmt,
        args=args,
    )
    assert args[STR.infmt] == vars(FORMAT)[fmt]


def test__check_template_render_vals_args_implicit_fail():
    # The values-file format cannot be deduced from the filename.
    args = {STR.valsfile: "a.jpg"}
    with raises(UWError) as e:
        cli._check_template_render_vals_args(args)
    assert "Cannot deduce format" in str(e.value)


def test__check_template_render_vals_args_implicit_pass():
    # The values-file format is deduced from the filename.
    args = {STR.valsfile: "a.yaml"}
    checked = cli._check_template_render_vals_args(args)
    assert checked[STR.valsfmt] == FORMAT.yaml


def test__check_template_render_vals_args_noop_no_valsfile():
    # No values file is provided, so format is irrelevant.
    args = {STR.valsfile: None}
    assert cli._check_template_render_vals_args(args) == args


def test__check_template_render_vals_args_noop_explicit_valsfmt():
    # An explicit values format is honored, valid or not.
    args = {STR.valsfile: "a.txt", STR.valsfmt: "jpg"}
    assert cli._check_template_render_vals_args(args) == args


def test__check_verbosity_fail(capsys):
    log.setLevel(logging.INFO)
    args = {STR.quiet: True, STR.verbose: True}
    with raises(SystemExit):
        cli._check_verbosity(args)
    assert "--quiet may not be used with --verbose" in capsys.readouterr().err


@pytest.mark.parametrize("flags", ([STR.quiet], [STR.verbose]))
def test__check_verbosity_ok(flags):
    args = {flag: True for flag in flags}
    assert cli._check_verbosity(args) == args


def test__dict_from_key_eq_val_strings():
    assert not cli._dict_from_key_eq_val_strings([])
    assert cli._dict_from_key_eq_val_strings(["a=1", "b=2"]) == {"a": "1", "b": "2"}


@pytest.mark.parametrize(
    "params",
    [
        (STR.compare, "_dispatch_config_compare"),
        (STR.realize, "_dispatch_config_realize"),
        (STR.validate, "_dispatch_config_validate"),
    ],
)
def test__dispatch_config(params):
    action, funcname = params
    args = {STR.action: action}
    with patch.object(cli, funcname) as func:
        cli._dispatch_config(args)
    func.assert_called_once_with(args)


def test__dispatch_config_compare():
    args = {STR.file1path: 1, STR.file1fmt: 2, STR.file2path: 3, STR.file2fmt: 4}
    with patch.object(cli.uwtools.api.config, "compare") as compare:
        cli._dispatch_config_compare(args)
    compare.assert_called_once_with(
        config_1_path=args[STR.file1path],
        config_1_format=args[STR.file1fmt],
        config_2_path=args[STR.file2path],
        config_2_format=args[STR.file2fmt],
    )


def test__dispatch_config_realize():
    args = {
        STR.infile: 1,
        STR.infmt: 2,
        STR.outfile: 3,
        STR.outfmt: 4,
        STR.suppfiles: 5,
        STR.valsneeded: 6,
        STR.total: 7,
        STR.dryrun: 8,
    }
    with patch.object(cli.uwtools.api.config, "realize") as realize:
        cli._dispatch_config_realize(args)
    realize.assert_called_once_with(
        input_config=1,
        input_format=2,
        output_file=3,
        output_format=4,
        supplemental_configs=5,
        values_needed=6,
        total=7,
        dry_run=8,
    )


def test__dispatch_config_realize_fail(caplog):
    log.setLevel(logging.ERROR)
    args = {
        x: None
        for x in (
            STR.infile,
            STR.infmt,
            STR.outfile,
            STR.outfmt,
            STR.suppfiles,
            STR.valsneeded,
            STR.total,
            STR.dryrun,
        )
    }
    with patch.object(cli.uwtools.api.config, "realize", side_effect=UWConfigRealizeError):
        assert cli._dispatch_config_realize(args) is False
    assert regex_logged(caplog, "Config could not be realized")


def test__dispatch_config_realize_no_optional():
    args = {
        STR.infile: None,
        STR.infmt: None,
        STR.outfile: None,
        STR.outfmt: None,
        STR.suppfiles: ["/foo.vals"],
        STR.valsneeded: False,
        STR.total: False,
        STR.dryrun: False,
    }
    with patch.object(cli.uwtools.api.config, "realize") as realize:
        cli._dispatch_config_realize(args)
    realize.assert_called_once_with(
        input_config=None,
        input_format=None,
        output_file=None,
        output_format=None,
        supplemental_configs=["/foo.vals"],
        values_needed=False,
        total=False,
        dry_run=False,
    )


def test__dispatch_config_validate_config_obj():
    config = uwtools.api.config._YAMLConfig(config={})
    _dispatch_config_validate_args = {STR.schemafile: 1, STR.infile: config}
    with patch.object(uwtools.api.config, "_validate_yaml") as _validate_yaml:
        cli._dispatch_config_validate(_dispatch_config_validate_args)
    _validate_yaml_args = {STR.schemafile: 1, STR.config: config}
    _validate_yaml.assert_called_once_with(**_validate_yaml_args)


def test__dispatch_fv3():
    args: dict = {
        "batch": True,
        "config_file": "config.yaml",
        "cycle": dt.datetime.now(),
        "dry_run": False,
        "graph_file": None,
    }
    with patch.object(uwtools.api.fv3, "execute") as execute:
        cli._dispatch_fv3({**args, "action": "foo"})
    execute.assert_called_once_with(**{**args, "task": "foo"})


def test__dispatch_mpas():
    args: dict = {
        "batch": True,
        "config_file": "config.yaml",
        "cycle": dt.datetime.now(),
        "dry_run": False,
        "graph_file": None,
    }
    with patch.object(uwtools.api.mpas, "execute") as execute:
        cli._dispatch_mpas({**args, "action": "foo"})
    execute.assert_called_once_with(**{**args, "task": "foo"})


@pytest.mark.parametrize(
    "params",
    [
        (STR.realize, "_dispatch_rocoto_realize"),
        (STR.validate, "_dispatch_rocoto_validate"),
    ],
)
def test__dispatch_rocoto(params):
    action, funcname = params
    args = {STR.action: action}
    with patch.object(cli, funcname) as func:
        cli._dispatch_rocoto(args)
    func.assert_called_once_with(args)


def test__dispatch_rocoto_realize():
    args = {STR.infile: 1, STR.outfile: 2}
    with patch.object(uwtools.api.rocoto, "_realize") as _realize:
        cli._dispatch_rocoto_realize(args)
    _realize.assert_called_once_with(config=1, output_file=2)


def test__dispatch_rocoto_realize_no_optional():
    args = {STR.infile: None, STR.outfile: None}
    with patch.object(uwtools.api.rocoto, "_realize") as func:
        cli._dispatch_rocoto_realize(args)
    func.assert_called_once_with(config=None, output_file=None)


def test__dispatch_rocoto_validate_xml():
    args = {STR.infile: 1}
    with patch.object(uwtools.api.rocoto, "_validate") as _validate:
        cli._dispatch_rocoto_validate(args)
    _validate.assert_called_once_with(xml_file=1)


def test__dispatch_rocoto_validate_xml_invalid():
    args = {STR.infile: 1, STR.verbose: False}
    with patch.object(uwtools.api.rocoto, "_validate", return_value=False):
        assert cli._dispatch_rocoto_validate(args) is False


def test__dispatch_rocoto_validate_xml_no_optional():
    args = {STR.infile: None, STR.verbose: False}
    with patch.object(uwtools.api.rocoto, "_validate") as validate:
        cli._dispatch_rocoto_validate(args)
    validate.assert_called_once_with(xml_file=None)


def test__dispatch_sfc_climo_gen():
    args: dict = {
        "batch": True,
        "config_file": "config.yaml",
        "dry_run": False,
        "graph_file": None,
    }
    with patch.object(uwtools.api.sfc_climo_gen, "execute") as execute:
        cli._dispatch_sfc_climo_gen({**args, "action": "foo"})
    execute.assert_called_once_with(**{**args, "task": "foo"})


@pytest.mark.parametrize(
    "params",
    [(STR.render, "_dispatch_template_render"), (STR.translate, "_dispatch_template_translate")],
)
def test__dispatch_template(params):
    action, funcname = params
    args = {STR.action: action}
    with patch.object(cli, funcname) as func:
        cli._dispatch_template(args)
    func.assert_called_once_with(args)


@pytest.mark.parametrize("valsneeded", [False, True])
def test__dispatch_template_render_fail(valsneeded):
    args = {
        STR.infile: 1,
        STR.outfile: 2,
        STR.valsfile: 3,
        STR.valsfmt: 4,
        STR.keyvalpairs: ["foo=88", "bar=99"],
        STR.env: 5,
        STR.valsneeded: valsneeded,
        STR.partial: 7,
        STR.dryrun: 8,
    }
    with patch.object(uwtools.api.template, "render", side_effect=UWTemplateRenderError):
        assert cli._dispatch_template_render(args) is valsneeded


def test__dispatch_template_render_no_optional():
    args: dict = {
        STR.infile: None,
        STR.outfile: None,
        STR.valsfile: None,
        STR.valsfmt: None,
        STR.keyvalpairs: [],
        STR.env: False,
        STR.valsneeded: False,
        STR.partial: False,
        STR.dryrun: False,
    }
    with patch.object(uwtools.api.template, "render") as render:
        cli._dispatch_template_render(args)
    render.assert_called_once_with(
        input_file=None,
        output_file=None,
        values_src=None,
        values_format=None,
        overrides={},
        env=False,
        values_needed=False,
        partial=False,
        dry_run=False,
    )


def test__dispatch_template_render_yaml():
    args = {
        STR.infile: 1,
        STR.outfile: 2,
        STR.valsfile: 3,
        STR.valsfmt: 4,
        STR.keyvalpairs: ["foo=88", "bar=99"],
        STR.env: 5,
        STR.valsneeded: 6,
        STR.partial: 7,
        STR.dryrun: 8,
    }
    with patch.object(uwtools.api.template, "render") as render:
        cli._dispatch_template_render(args)
    render.assert_called_once_with(
        input_file=1,
        output_file=2,
        values_src=3,
        values_format=4,
        overrides={"foo": "88", "bar": "99"},
        env=5,
        values_needed=6,
        partial=7,
        dry_run=8,
    )


def test__dispatch_template_translate():
    args = {
        STR.infile: 1,
        STR.outfile: 2,
        STR.dryrun: 3,
    }
    with patch.object(
        uwtools.api.template, "_convert_atparse_to_jinja2"
    ) as _convert_atparse_to_jinja2:
        cli._dispatch_template_translate(args)
    _convert_atparse_to_jinja2.assert_called_once_with(input_file=1, output_file=2, dry_run=3)


def test__dispatch_template_translate_no_optional():
    args = {
        STR.dryrun: False,
        STR.infile: None,
        STR.outfile: None,
    }
    with patch.object(
        uwtools.api.template, "_convert_atparse_to_jinja2"
    ) as _convert_atparse_to_jinja2:
        cli._dispatch_template_translate(args)
    _convert_atparse_to_jinja2.assert_called_once_with(
        input_file=None, output_file=None, dry_run=False
    )


@pytest.mark.parametrize("quiet", [False, True])
@pytest.mark.parametrize("verbose", [False, True])
def test_main_fail_checks(capsys, quiet, verbose):
    # Using mode 'template render' for testing.
    raw_args = ["testing", STR.template, STR.render]
    if quiet:
        raw_args.append(cli._switch(STR.quiet))
    if verbose:
        raw_args.append(cli._switch(STR.verbose))
    with patch.object(sys, "argv", raw_args):
        with patch.object(cli, "_dispatch_template", return_value=True):
            with raises(SystemExit) as e:
                cli.main()
            if quiet and verbose:
                assert e.value.code == 1
                assert "--quiet may not be used with --verbose" in capsys.readouterr().err
            else:
                assert e.value.code == 0


@pytest.mark.parametrize("vals", [(True, 0), (False, 1)])
def test_main_fail_dispatch(vals):
    # Using mode 'template render' for testing.
    dispatch_retval, exit_status = vals
    raw_args = ["testing", STR.template, STR.render]
    with patch.object(sys, "argv", raw_args):
        with patch.object(cli, "_dispatch_template", return_value=dispatch_retval):
            with raises(SystemExit) as e:
                cli.main()
            assert e.value.code == exit_status


def test_main_fail_exception_abort():
    # Mock setup_logging() to raise a UWError in main() before logging is configured, which triggers
    # a call to _abort().
    msg = "Catastrophe"
    with patch.object(cli, "setup_logging", side_effect=UWError(msg)):
        with patch.object(cli, "_abort", side_effect=SystemExit) as _abort:
            with raises(SystemExit):
                cli.main()
        _abort.assert_called_once_with(msg)


def test_main_fail_exception_log():
    # Mock _dispatch_template() to raise a UWError in main() after logging is configured, which logs
    # an error message and exists with exit status.
    msg = "Catastrophe"
    with patch.object(cli, "_dispatch_template", side_effect=UWError(msg)):
        with patch.object(cli, "log") as log:
            with patch.object(sys, "argv", ["uw", "template", "render"]):
                with raises(SystemExit) as e:
                    cli.main()
                assert e.value.code == 1
            assert log.called_once_with(msg)


def test__parse_args():
    raw_args = ["testing", "--bar", "88"]
    with patch.object(cli, "Parser") as Parser:
        cli._parse_args(raw_args)
        Parser.assert_called_once()
        parser = Parser()
        parser.parse_args.assert_called_with(raw_args)


# Helper functions


def actions(parser: Parser) -> List[str]:
    # Return actions (named subparsers) belonging to the given parser.
    if actions := [x for x in parser._actions if isinstance(x, _SubParsersAction)]:
        return list(actions[0].choices.keys())
    return []


@fixture
def subparsers():
    # Create and return a subparsers test object.
    return Parser().add_subparsers()
