# pylint: disable=missing-function-docstring,redefined-outer-name

from argparse import ArgumentError

import pytest
from pytest import fixture, raises

from uwtools.cli import set_config


@fixture
def args(tmp_path):
    for fn in ("in", "cfg", "log", "out"):
        with (tmp_path / fn).open("w"):
            pass
    return [
        "--input-base-file",
        str(tmp_path / "in"),
        "--config-file",
        str(tmp_path / "cfg"),
        "--log-file",
        str(tmp_path / "log"),
        "--outfile",
        str(tmp_path / "out"),
    ]


def test_parse_args_base(args):
    parsed = set_config.parse_args(args)
    assert not parsed.config_file_type
    assert not parsed.dry_run
    assert not parsed.input_file_type
    assert not parsed.output_file_type
    assert not parsed.quiet
    assert not parsed.show_format
    assert not parsed.values_needed
    assert not parsed.verbose
    assert parsed.config_file.endswith("/cfg")
    assert parsed.input_base_file.endswith("/in")
    assert parsed.log_file.endswith("/log")
    assert parsed.outfile.endswith("/out")


def test_parse_args_file_type_output_fieldtable(args):
    args += ["--output-file-type", "FieldTable"]
    parsed = set_config.parse_args(args)
    assert parsed.output_file_type == "FieldTable"


@pytest.mark.parametrize("opt", ["--config-file-type", "--input-file-type", "--output-file-type"])
def test_parse_args_file_types_bad(opt, args):
    args += [opt, "FOO"]
    with raises(SystemExit):
        set_config.parse_args(args)


@pytest.mark.parametrize("fmt", ["F90", "INI", "YAML"])
def test_parse_args_file_types_good(fmt, args):
    args += ["--config-file-type", fmt, "--input-file-type", fmt, "--output-file-type", fmt]
    parsed = set_config.parse_args(args)
    assert parsed.config_file_type == fmt
    assert parsed.input_file_type == fmt
    assert parsed.output_file_type == fmt


def test_parse_args_mutually_exclusive_1(args):
    args += ["--dry-run", "--quiet"]
    with raises(ArgumentError):
        set_config.parse_args(args)


def test_parse_args_mutually_inclusive_1(args):
    # Remove "--outfile" and its value, add "--show-format".
    args = args[:7] + ["--show-format"]
    with raises(SystemExit):
        set_config.parse_args(args)
