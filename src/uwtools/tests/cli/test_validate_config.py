# pylint: disable=duplicate-code,missing-function-docstring,redefined-outer-name
"""
Tests for the validate-config CLI.
"""

import logging
from types import SimpleNamespace as ns
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools.cli import validate_config
from uwtools.tests.support import fixture_path

# NB: Ensure that at least one test exercises both short and long forms of each
#     CLI switch.


@fixture
def files(tmp_path):
    cfgfile = tmp_path / "cfg.yaml"
    schemafile = fixture_path("schema_test_good.yaml")
    cfgfile.touch()
    return str(cfgfile), str(schemafile)


def test_main(files):
    with patch.object(validate_config, "parse_args") as parse_args:
        cfgfile, schemafile = files
        parse_args.return_value = ns(
            config_file=cfgfile,
            quiet=False,
            validation_schema=schemafile,
            verbose=False,
        )
        with patch.object(validate_config, "config_is_valid") as config_is_valid:
            with raises(SystemExit) as e:
                validate_config.main()
            assert e.value.code == 0
            config_is_valid.assert_called_once_with(
                config_file=cfgfile, schema_file=schemafile
            )


@pytest.mark.parametrize("sw", [ns(c="-c", s="-s"), ns(c="--config-file", s="--validation-schema")])
def test_parse_args_bad_cfgfile(capsys, files, sw, tmp_path):
    """
    Fails if non-existent config file is specified.
    """
    _, schemafile = files
    cfgfile = str(tmp_path / "no-such-file")
    with raises(FileNotFoundError):
        validate_config.parse_args([sw.c, cfgfile, sw.s, schemafile])
    assert f"{cfgfile} does not exist" in capsys.readouterr().err


@pytest.mark.parametrize("sw", [ns(c="-c", s="-s"), ns(c="--config-file", s="--validation-schema")])
def test_parse_args_bad_schemafile(capsys, files, sw, tmp_path):
    """
    Fails if non-existent schema file is specified.
    """
    logging.getLogger().setLevel(logging.INFO)
    cfgfile, _ = files
    schemafile = str(tmp_path / "no-such-file")
    with raises(FileNotFoundError):
        validate_config.parse_args([sw.c, cfgfile, sw.s, schemafile])
    assert f"{schemafile} does not exist" in capsys.readouterr().err


@pytest.mark.parametrize("noise", ["-q", "--quiet", "-v", "--verbose"])
@pytest.mark.parametrize(
    "sw",
    [ns(c="-c", l="-l", s="-s"), ns(c="--config-file", s="--validation-schema")],
)
def test_parse_args_good(files, noise, sw):
    """
    Test all valid CLI switch/value combinations.
    """
    cfgfile, schemafile = files
    cfgtype = "F90"  # representative (not exhaustive) value
    parsed = validate_config.parse_args(
        [sw.c, cfgfile, sw.s, schemafile, "--config-file-type", cfgtype, noise]
    )
    assert parsed.config_file == cfgfile
    assert parsed.validation_schema == schemafile
    if noise in ["-q", "--quiet"]:
        sw_off = parsed.verbose
        sw_on = parsed.quiet
    else:
        sw_off = parsed.quiet
        sw_on = parsed.verbose
    assert sw_off is False
    assert sw_on is True
    assert parsed.config_file_type == cfgtype


@pytest.mark.parametrize(
    "sw",
    [
        ns(c="-c", q="-q", s="-s", v="-v"),
        ns(c="--config-file", q="--quiet", s="--validation-schema", v="--verbose"),
    ],
)
def test_parse_args_mutually_exclusive_args(capsys, files, sw):
    cfgfile, schemafile = files
    with raises(SystemExit) as e:
        validate_config.parse_args([sw.c, cfgfile, sw.s, schemafile, sw.q, sw.v])
    assert e.value.code == 1
    assert "Options --dry-run and --outfile may not be used together" in capsys.readouterr().err
