# pylint: disable=duplicate-code,missing-function-docstring,redefined-outer-name
"""
Tests for the set-config CLI.
"""

from argparse import ArgumentError
from itertools import chain
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools.cli import set_config


@fixture
def args(tmp_path):
    for fn in ("in.yaml", "cfg.yaml", "out.yaml"):
        (tmp_path / fn).touch()
    return {
        "--input-base-file": str(tmp_path / "in.yaml"),
        "--config-file": str(tmp_path / "cfg.yaml"),
        "--outfile": str(tmp_path / "out.yaml"),
    }


@patch.object(set_config.config, "create_config_obj")
def test_main(create_config_obj, args):
    arglist = list(chain(*args.items()))
    with patch.object(set_config.sys, "argv", ["test", *arglist]):
        # Test success:
        set_config.main()
        create_config_obj.assert_called_once_with(
            input_base_file=args["--input-base-file"],
            compare=False,
            config_file=args["--config-file"],
            config_file_type=None,
            dry_run=False,
            input_file_type=None,
            outfile=args["--outfile"],
            output_file_type=None,
            show_format=False,
            values_needed=False,
        )
        # Test failure:
        create_config_obj.side_effect = set_config.UWConfigError()
        with patch.object(set_config.sys, "exit") as exit_:
            set_config.main()
            assert exit_.called_once_with("")


def test_parse_args_base(args):
    arglist = list(chain(*args.items()))
    parsed = set_config.parse_args(arglist)
    assert not parsed.config_file_type
    assert not parsed.dry_run
    assert not parsed.input_file_type
    assert not parsed.output_file_type
    assert not parsed.quiet
    assert not parsed.show_format
    assert not parsed.values_needed
    assert not parsed.verbose
    assert parsed.config_file.endswith("/cfg.yaml")
    assert parsed.input_base_file.endswith("/in.yaml")
    assert parsed.outfile.endswith("/out.yaml")


def test_parse_args_file_type_output_fieldtable(args):
    args["--output-file-type"] = "FieldTable"
    arglist = list(chain(*args.items()))
    parsed = set_config.parse_args(arglist)
    assert parsed.output_file_type == "FieldTable"


@pytest.mark.parametrize("opt", ["--config-file-type", "--input-file-type", "--output-file-type"])
def test_parse_args_file_types_bad(opt, args):
    args[opt] = "FOO"
    arglist = list(chain(*args.items()))
    with raises(SystemExit):
        set_config.parse_args(arglist)


@pytest.mark.parametrize("fmt", ["F90", "INI", "YAML"])
def test_parse_args_file_types_good(fmt, args):
    args = {**args, "--config-file-type": fmt, "--input-file-type": fmt, "--output-file-type": fmt}
    arglist = list(chain(*args.items()))
    parsed = set_config.parse_args(arglist)
    assert parsed.config_file_type == fmt
    assert parsed.input_file_type == fmt
    assert parsed.output_file_type == fmt


def test_parse_args_mutually_exclusive(args):
    arglist = list(chain(*args.items())) + ["--dry-run", "--quiet"]
    with raises(ArgumentError):
        set_config.parse_args(arglist)


def test_parse_args_mutually_inclusive(args):
    del args["--outfile"]
    arglist = list(chain(*args.items()))
    arglist += ["--show-format"]
    with raises(ArgumentError):
        set_config.parse_args(arglist)
