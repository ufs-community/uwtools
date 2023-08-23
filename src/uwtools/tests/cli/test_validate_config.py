# pylint: disable=duplicate-code,missing-function-docstring,redefined-outer-name
"""
Tests for the validate-config CLI.
"""

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
    config_file = tmp_path / "cfg.yaml"
    schema_file = fixture_path("schema_test_good.yaml")
    config_file.touch()
    return str(config_file), str(schema_file)


def test_main(files):
    with patch.object(validate_config, "parse_args") as parse_args:
        config_file, schema_file = files
        parse_args.return_value = ns(
            config_file=config_file,
            quiet=False,
            validation_schema=schema_file,
            verbose=False,
        )
        with patch.object(validate_config, "config_is_valid") as config_is_valid:
            with raises(SystemExit) as e:
                validate_config.main()
            assert e.value.code == 0
            config_is_valid.assert_called_once_with(
                config_file=config_file, schema_file=schema_file
            )


@pytest.mark.parametrize("sw", [ns(c="-c", s="-s"), ns(c="--config-file", s="--validation-schema")])
def test_parse_args_bad_config_file(capsys, files, sw, tmp_path):
    """
    Fails if non-existent config file is specified.
    """
    _, schema_file = files
    config_file = str(tmp_path / "no-such-file")
    with raises(FileNotFoundError):
        validate_config.parse_args([sw.c, config_file, sw.s, schema_file])
    assert f"{config_file} does not exist" in capsys.readouterr().err


@pytest.mark.parametrize("sw", [ns(c="-c", s="-s"), ns(c="--config-file", s="--validation-schema")])
def test_parse_args_bad_schema_file(capsys, files, sw, tmp_path):
    """
    Fails if non-existent schema file is specified.
    """
    config_file, _ = files
    schema_file = str(tmp_path / "no-such-file")
    with raises(FileNotFoundError):
        validate_config.parse_args([sw.c, config_file, sw.s, schema_file])
    assert f"{schema_file} does not exist" in capsys.readouterr().err


@pytest.mark.parametrize("noise", ["-q", "--quiet", "-v", "--verbose"])
@pytest.mark.parametrize(
    "sw",
    [ns(c="-c", l="-l", s="-s"), ns(c="--config-file", s="--validation-schema")],
)
def test_parse_args_good(files, noise, sw):
    """
    Test all valid CLI switch/value combinations.
    """
    config_file, schema_file = files
    cfgtype = "F90"  # representative (not exhaustive) value
    parsed = validate_config.parse_args(
        [sw.c, config_file, sw.s, schema_file, "--config-file-type", cfgtype, noise]
    )
    assert parsed.config_file == config_file
    assert parsed.validation_schema == schema_file
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
    config_file, schema_file = files
    with raises(SystemExit) as e:
        validate_config.parse_args([sw.c, config_file, sw.s, schema_file, sw.q, sw.v])
    assert e.value.code == 1
    assert "Options --quiet and --verbose may not be used together" in capsys.readouterr().err
