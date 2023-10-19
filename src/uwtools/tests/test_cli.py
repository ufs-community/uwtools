# pylint: disable=missing-function-docstring,protected-access,redefined-outer-name

import logging
import sys
from argparse import ArgumentParser as Parser
from argparse import Namespace as ns
from argparse import _SubParsersAction
from typing import List
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools import cli
from uwtools.cli import STR
from uwtools.logging import log
from uwtools.utils.file import FORMAT

# Test functions


def test__abort(capsys):
    msg = "Aborting..."
    with raises(SystemExit):
        cli._abort(msg)
    assert msg in capsys.readouterr().err


def test__add_subparser_config(subparsers):
    cli._add_subparser_config(subparsers)
    assert submodes(subparsers.choices[STR.config]) == [
        STR.compare,
        STR.realize,
        STR.translate,
        STR.validate,
    ]


def test__add_subparser_config_compare(subparsers):
    cli._add_subparser_config_compare(subparsers)
    assert subparsers.choices[STR.compare]


def test__add_subparser_config_realize(subparsers):
    cli._add_subparser_config_realize(subparsers)
    assert subparsers.choices[STR.realize]


def test__add_subparser_config_translate(subparsers):
    cli._add_subparser_config_translate(subparsers)
    assert subparsers.choices[STR.translate]


def test__add_subparser_config_validate(subparsers):
    cli._add_subparser_config_validate(subparsers)
    assert subparsers.choices[STR.validate]


def test__add_subparser_forecast(subparsers):
    cli._add_subparser_forecast(subparsers)
    assert submodes(subparsers.choices[STR.forecast]) == [STR.run]


def test__add_subparser_forecast_run(subparsers):
    cli._add_subparser_forecast_run(subparsers)
    assert subparsers.choices[STR.run]


def test__add_subparser_template(subparsers):
    cli._add_subparser_template(subparsers)
    assert submodes(subparsers.choices[STR.template]) == [STR.render]


def test__add_subparser_template_render(subparsers):
    cli._add_subparser_template_render(subparsers)
    assert subparsers.choices[STR.render]


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
    args = ns()
    vars(args).update({file_arg: None, format_arg: None})
    with raises(SystemExit):
        cli._check_file_vs_format(file_arg=file_arg, format_arg=format_arg, args=args)
    assert (
        "Specify %s when %s is not specified" % (cli._switch(format_arg), cli._switch(file_arg))
        in capsys.readouterr().err
    )


def test__check_file_vs_format_pass_explicit():
    # Accept explcitly-specified format, whatever it is.
    fmt = "jpg"
    args = ns()
    vars(args).update({STR.infile: "/path/to/input.txt", STR.infmt: fmt})
    args = cli._check_file_vs_format(
        file_arg=STR.infile,
        format_arg=STR.infmt,
        args=args,
    )
    assert args.input_format == fmt


@pytest.mark.parametrize("fmt", vars(FORMAT).keys())
def test__check_file_vs_format_pass_implicit(fmt):
    # The format is correctly deduced for a file with a known extension.
    args = ns()
    vars(args).update({STR.infile: f"/path/to/input.{fmt}", STR.infmt: None})
    args = cli._check_file_vs_format(
        file_arg=STR.infile,
        format_arg=STR.infmt,
        args=args,
    )
    assert args.input_format == vars(FORMAT)[fmt]


def test__check_quiet_vs_verbose_fail(capsys):
    log.setLevel(logging.INFO)
    args = ns()
    vars(args).update({STR.quiet: True, STR.verbose: True})
    with raises(SystemExit):
        cli._check_quiet_vs_verbose(args)
    assert (
        "Specify at most one of %s, %s" % (cli._switch(STR.quiet), cli._switch(STR.verbose))
        in capsys.readouterr().err
    )


def test__check_quiet_vs_verbose_ok():
    args = ns(foo=88)
    assert cli._check_quiet_vs_verbose(args) == args


def test__check_template_render_vals_args_implicit_fail():
    # The values-file format cannot be deduced from the filename.
    args = ns()
    vars(args)[STR.valsfile] = "a.jpg"
    with raises(ValueError) as e:
        cli._check_template_render_vals_args(args)
    assert "Cannot deduce format" in str(e.value)


def test__check_template_render_vals_args_implicit_pass():
    # The values-file format is deduced from the filename.
    args = ns()
    vars(args)[STR.valsfile] = "a.yaml"
    checked = cli._check_template_render_vals_args(args)
    assert vars(checked)[STR.valsfmt] == FORMAT.yaml


def test__check_template_render_vals_args_noop_no_valsfile():
    # No values file is provided, so format is irrelevant.
    args = ns()
    vars(args)[STR.valsfile] = None
    assert cli._check_template_render_vals_args(args) == args


def test__check_template_render_vals_args_noop_explicit_valsfmt():
    # An explicit values format is honored, valid or not.
    args = ns()
    vars(args)[STR.valsfile] = "a.txt"
    vars(args)[STR.valsfmt] = "jpg"
    assert cli._check_template_render_vals_args(args) == args


def test__dict_from_key_eq_val_strings():
    assert not cli._dict_from_key_eq_val_strings([])
    assert cli._dict_from_key_eq_val_strings(["a=1", "b=2"]) == {"a": "1", "b": "2"}


@pytest.mark.parametrize(
    "params",
    [
        (STR.compare, "_dispatch_config_compare"),
        (STR.realize, "_dispatch_config_realize"),
        (STR.translate, "_dispatch_config_translate"),
        (STR.validate, "_dispatch_config_validate"),
    ],
)
def test__dispatch_config(params):
    submode, funcname = params
    args = ns()
    vars(args).update({STR.submode: submode})
    with patch.object(cli, funcname) as func:
        cli._dispatch_config(args)
    assert func.called_once_with(args)


def test__dispatch_config_compare():
    args = ns()
    vars(args).update({STR.file1path: 1, STR.file1fmt: 2, STR.file2path: 3, STR.file2fmt: 4})
    with patch.object(cli.uwtools.config.core, "compare_configs") as compare_configs:
        cli._dispatch_config_compare(args)
    assert compare_configs.called_once_with(args)


def test__dispatch_config_realize():
    args = ns()
    vars(args).update(
        {
            STR.infile: 1,
            STR.infmt: 2,
            STR.outfile: 3,
            STR.outfmt: 4,
            STR.valsfile: 5,
            STR.valsfmt: 6,
            STR.valsneeded: 7,
            STR.dryrun: 8,
        }
    )
    with patch.object(cli.uwtools.config.core, "realize_config") as realize_config:
        cli._dispatch_config_realize(args)
    assert realize_config.called_once_with(args)


def test__dispatch_config_translate_arparse_to_jinja2():
    args = ns()
    vars(args).update(
        {
            STR.infile: 1,
            STR.infmt: FORMAT.atparse,
            STR.outfile: 3,
            STR.outfmt: FORMAT.jinja2,
            STR.dryrun: 5,
        }
    )
    with patch.object(cli.uwtools.config.atparse_to_jinja2, "convert") as convert:
        cli._dispatch_config_translate(args)
    assert convert.called_once_with(args)


def test__dispatch_config_translate_unsupported():
    args = ns()
    vars(args).update(
        {STR.infile: 1, STR.infmt: "jpg", STR.outfile: 3, STR.outfmt: "png", STR.dryrun: 5}
    )
    assert cli._dispatch_config_translate(args) is False


def test__dispatch_config_validate_yaml():
    args = ns()
    vars(args).update({STR.infile: 1, STR.infmt: FORMAT.yaml, STR.schemafile: 3})
    with patch.object(cli.uwtools.config.validator, "validate_yaml") as validate_yaml:
        cli._dispatch_config_validate(args)
    assert validate_yaml.called_once_with(args)


def test__dispatch_config_validate_unsupported():
    args = ns()
    vars(args).update({STR.infile: 1, STR.infmt: "jpg", STR.schemafile: 3})
    assert cli._dispatch_config_validate(args) is False


@pytest.mark.parametrize("params", [(STR.run, "_dispatch_forecast_run")])
def test__dispatch_forecast(params):
    submode, funcname = params
    args = ns()
    vars(args).update({STR.submode: submode})
    with patch.object(cli, funcname) as module:
        cli._dispatch_forecast(args)
    assert module.called_once_with(args)


def test__dispatch_forecast_run():
    args = ns(
        batch_script=None,
        cycle="2023-01-01T00:00:00",
        config_file=1,
        dry_run=True,
        forecast_model="foo",
    )
    vars(args).update({STR.cfgfile: 1, "forecast_model": "foo"})
    with patch.object(cli.uwtools.drivers.forecast, "FooForecast", create=True) as FooForecast:
        CLASSES = {"foo": getattr(cli.uwtools.drivers.forecast, "FooForecast")}
        with patch.object(cli.uwtools.drivers.forecast, "CLASSES", new=CLASSES):
            cli._dispatch_forecast_run(args)
    assert FooForecast.called_once_with(args)
    FooForecast().run.assert_called_once_with(cycle="2023-01-01T00:00:00")


@pytest.mark.parametrize(
    "params",
    [
        (STR.realize, "_dispatch_rocoto_realize"),
        (STR.validate, "_dispatch_rocoto_validate"),
    ],
)
def test__dispatch_rocoto(params):
    submode, funcname = params
    args = ns()
    vars(args).update({STR.submode: submode})
    with patch.object(cli, funcname) as module:
        cli._dispatch_rocoto(args)
    assert module.called_once_with(args)


def test__dispatch_rocoto_realize():
    args = ns()
    vars(args).update({STR.infile: 1, STR.outfile: 2})
    with patch.object(cli.uwtools.rocoto, "realize_rocoto_xml") as module:
        cli._dispatch_rocoto_realize(args)
    assert module.called_once_with(args)


def test__dispatch_rocoto_realize_invalid():
    args = ns()
    vars(args).update(
        {
            STR.infile: 1,
            STR.outfile: 2,
        }
    )
    with patch.object(cli.uwtools.rocoto, "realize_rocoto_xml", return_value=False):
        assert cli._dispatch_rocoto_realize(args) is False


def test__dispatch_rocoto_validate_xml():
    args = ns()
    vars(args).update({STR.infile: 1})
    with patch.object(cli.uwtools.rocoto, "validate_rocoto_xml") as validate:
        cli._dispatch_rocoto_validate(args)
    assert validate.called_once_with(args)


def test__dispatch_rocoto_validate_xml_invalid():
    args = ns()
    vars(args).update({STR.infile: 1, STR.verbose: False})
    with patch.object(cli.uwtools.rocoto, "validate_rocoto_xml", return_value=False):
        assert cli._dispatch_rocoto_validate(args) is False


@pytest.mark.parametrize("params", [(STR.render, "_dispatch_template_render")])
def test__dispatch_template(params):
    submode, funcname = params
    args = ns()
    vars(args).update({STR.submode: submode})
    with patch.object(cli, funcname) as func:
        cli._dispatch_template(args)
    assert func.called_once_with(args)


def test__dispatch_template_render_yaml():
    args = ns()
    vars(args).update(
        {
            STR.infile: 1,
            STR.outfile: 2,
            STR.valsfile: 3,
            STR.valsfmt: 4,
            STR.keyvalpairs: ["foo=88", "bar=99"],
            STR.valsneeded: 6,
            STR.dryrun: 7,
        }
    )
    with patch.object(cli.uwtools.config.templater, STR.render) as templater:
        cli._dispatch_template_render(args)
    assert templater.called_once_with(args)


@pytest.mark.parametrize("quiet", [True])
@pytest.mark.parametrize("verbose", [False])
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
                assert "Specify at most one of" in capsys.readouterr().err
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


def test_main_raises_exception(capsys):
    msg = "Test failed intentionally"
    with patch.object(cli, "_parse_args", side_effect=Exception(msg)):
        with raises(SystemExit):
            cli.main()
    assert msg in capsys.readouterr().err


def test__parse_args():
    raw_args = ["testing", "--bar", "88"]
    with patch.object(cli, "Parser") as Parser:
        cli._parse_args(raw_args)
        Parser.assert_called_once()
        parser = Parser()
        parser.parse_args.assert_called_with(raw_args)


# Helper functions


def submodes(parser: Parser) -> List[str]:
    # Return submodes (named subparsers) belonging to the given parser. For some background, see
    # https://stackoverflow.com/questions/43688450.
    if actions := [x for x in parser._actions if isinstance(x, _SubParsersAction)]:
        return list(actions[0].choices.keys())
    return []


@fixture
def subparsers():
    # Create and return a subparsers test object.
    return Parser().add_subparsers()
