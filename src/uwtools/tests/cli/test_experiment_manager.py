# pylint: disable=duplicate-code,missing-function-docstring,redefined-outer-name
"""
Tests for the experiment-manager CLI.
"""

import logging
from types import SimpleNamespace as ns
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools.cli import experiment_manager
from uwtools.tests.support import logged

# NB: Ensure that at least one test exercises both short and long forms of each
#     CLI switch.


def test_main():
    with patch.object(experiment_manager, "parse_args") as parse_args:
        cfgfile = "/some/file"
        parse_args.return_value = ns(forecast_app="SRW", config_file=cfgfile)
        with patch.object(experiment_manager.experiment, "SRWExperiment") as experiment:
            experiment_manager.main()
        experiment.assert_called_once_with(cfgfile)


@fixture
def cfgfile(tmp_path):
    path = tmp_path / "cfg.yaml"
    path.touch()
    return str(path)


@pytest.mark.parametrize("sw", [ns(a="-a", c="-c"), ns(a="--forecast-app", c="--config-file")])
def test_parse_args_bad_app(caplog, cfgfile, sw):
    """
    Fails if a bad app name is specified.
    """
    with raises(SystemExit) as e:
        experiment_manager.parse_args([sw.a, "FOO", sw.c, cfgfile])
    assert e.value.code == 2
    assert logged(caplog, "invalid choice: 'FOO'")


@pytest.mark.parametrize("sw", [ns(a="-a", c="-c"), ns(a="--forecast-app", c="--config-file")])
def test_parse_args_bad_cfgfile(capsys, sw, tmp_path):
    """
    Fails if non-existent config file is specified.
    """
    cfgfile = str(tmp_path / "no-such-file")
    with raises(FileNotFoundError):
        experiment_manager.parse_args([sw.a, "SRW", sw.c, cfgfile])
    assert f"{cfgfile} does not exist" in capsys.readouterr().err


@pytest.mark.parametrize("noise", ["-q", "--quiet", "-v", "--verbose"])
@pytest.mark.parametrize("sw", [ns(a="-a", c="-c"), ns(a="--forecast-app", c="--config-file")])
def test_parse_args_good(cfgfile, noise, sw):
    """
    Test all valid CLI switch/value combinations.
    """
    parsed = experiment_manager.parse_args([sw.a, "SRW", sw.c, cfgfile, noise])
    assert parsed.forecast_app == "SRW"
    assert parsed.config_file == cfgfile
    if noise in ["-q", "--quiet"]:
        sw_off = parsed.verbose
        sw_on = parsed.quiet
    else:
        sw_off = parsed.quiet
        sw_on = parsed.verbose
    assert sw_off is False
    assert sw_on is True


@pytest.mark.parametrize(
    "sw",
    [
        ns(a="-a", c="-c", q="-q", v="-v"),
        ns(a="--forecast-app", c="--config-file", q="--quiet", v="--verbose"),
    ],
)
def test_parse_args_mutually_exclusive_args(capsys, cfgfile, sw):
    logging.getLogger().setLevel(logging.DEBUG)
    with raises(SystemExit) as e:
        experiment_manager.parse_args([sw.a, "SRW", sw.c, cfgfile, sw.q, sw.v])
    assert e.value.code == 1
    assert "Options --dry-run and --outfile may not be used together" in capsys.readouterr().err
