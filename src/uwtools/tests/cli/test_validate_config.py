# pylint: disable=duplicate-code,missing-function-docstring,redefined-outer-name
"""
Tests for the validate-config CLI.
"""

from types import SimpleNamespace as ns
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools.cli import validate_config
from uwtools.logger import Logger
from uwtools.tests.support import fixture_path

# NB: Ensure that at least one test exercises both short and long forms of each
#     CLI switch.


@fixture
def files(tmp_path):
    cfgfile = tmp_path / "cfg.yaml"
    logfile = tmp_path / "log"
    schemafile = fixture_path("schema_test_good.yaml")
    for path in cfgfile, logfile:
        path.touch()
    return str(cfgfile), str(logfile), str(schemafile)


def test_main(files):
    with patch.object(validate_config, "parse_args") as parse_args:
        cfgfile, logfile, schemafile = files
        log = Logger()
        parse_args.return_value = ns(
            config_file=cfgfile,
            log_file=logfile,
            quiet=False,
            validation_schema=schemafile,
            verbose=False,
        )
        with patch.object(validate_config, "config_is_valid") as config_is_valid:
            with patch.object(validate_config.cli_helpers, "setup_logging") as setup_logging:
                setup_logging.return_value = log
                with raises(SystemExit) as e:
                    validate_config.main()
                assert e.value.code == 0
            config_is_valid.assert_called_once_with(
                config_file=cfgfile, validation_schema=schemafile, log=log
            )


@pytest.mark.parametrize("sw", [ns(c="-c", s="-s"), ns(c="--config-file", s="--validation-schema")])
def test_parse_args_bad_cfgfile(sw, files, capsys, tmp_path):
    """
    Fails if non-existent config file is specified.
    """
    _, _, schemafile = files
    cfgfile = str(tmp_path / "no-such-file")
    with raises(SystemExit) as e:
        validate_config.parse_args([sw.c, cfgfile, sw.s, schemafile])
    assert e.value.code == 2
    assert "does not exist" in capsys.readouterr().err


@pytest.mark.parametrize("sw", [ns(c="-c", s="-s"), ns(c="--config-file", s="--validation-schema")])
def test_parse_args_bad_schemafile(sw, files, capsys, tmp_path):
    """
    Fails if non-existent schema file is specified.
    """
    cfgfile, _, _ = files
    schemafile = str(tmp_path / "no-such-file")
    with raises(SystemExit) as e:
        validate_config.parse_args([sw.c, cfgfile, sw.s, schemafile])
    assert e.value.code == 2
    assert "does not exist" in capsys.readouterr().err


@pytest.mark.parametrize("noise", ["-q", "--quiet", "-v", "--verbose"])
@pytest.mark.parametrize(
    "sw",
    [ns(c="-c", l="-l", s="-s"), ns(c="--config-file", l="--log-file", s="--validation-schema")],
)
def test_parse_args_good(sw, noise, files):
    """
    Test all valid CLI switch/value combinations.
    """
    cfgfile, logfile, schemafile = files
    cfgtype = "F90"  # representative (not exhaustive) value
    parsed = validate_config.parse_args(
        [sw.c, cfgfile, sw.l, logfile, sw.s, schemafile, "--config-file-type", cfgtype, noise]
    )
    assert parsed.config_file == cfgfile
    assert parsed.log_file == logfile
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
def test_parse_args_mutually_exclusive_args(sw, files, capsys):
    cfgfile, _, schemafile = files
    with raises(SystemExit) as e:
        validate_config.parse_args([sw.c, cfgfile, sw.s, schemafile, sw.q, sw.v])
    assert e.value.code == 1
    assert "Options --dry-run and --outfile may not be used together" in capsys.readouterr().err
