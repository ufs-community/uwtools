# pylint: disable=duplicate-code,missing-function-docstring,redefined-outer-name
"""
Tests for the experiment-manager CLI.
"""

from types import SimpleNamespace as ns
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools.cli import experiment_manager

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
def assets(tmp_path):
    cfgfile = tmp_path / "cfg.yaml"
    cfgfile.touch()
    logfile = tmp_path / "log"
    return str(cfgfile), str(logfile)


@pytest.mark.parametrize("sw", [ns(a="-a", c="-c"), ns(a="--forecast-app", c="--config-file")])
def test_parse_args_bad_app(sw, assets, capsys):
    """
    Fails if a bad app name is specified.
    """
    cfgfile, _ = assets
    with raises(SystemExit) as e:
        experiment_manager.parse_args([sw.a, "FOO", sw.c, cfgfile])
    assert e.value.code == 2
    assert "invalid choice: 'FOO'" in capsys.readouterr().err


@pytest.mark.parametrize("sw", [ns(a="-a", c="-c"), ns(a="--forecast-app", c="--config-file")])
def test_parse_args_bad_cfgfile(sw, capsys, tmp_path):
    """
    Fails if non-existent config file is specified.
    """
    cfgfile = str(tmp_path / "no-such-file")
    with raises(SystemExit) as e:
        experiment_manager.parse_args([sw.a, "SRW", sw.c, cfgfile])
    assert e.value.code == 2
    assert "does not exist" in capsys.readouterr().err


@pytest.mark.parametrize("noise", ["-q", "--quiet", "-v", "--verbose"])
@pytest.mark.parametrize(
    "sw", [ns(a="-a", c="-c", l="-l"), ns(a="--forecast-app", c="--config-file", l="--log-file")]
)
def test_parse_args_good(sw, noise, assets):
    """
    Test all valid CLI switch/value combinations.
    """
    cfgfile, logfile = assets
    parsed = experiment_manager.parse_args([sw.a, "SRW", sw.c, cfgfile, sw.l, logfile, noise])
    assert parsed.forecast_app == "SRW"
    assert parsed.config_file == cfgfile
    assert parsed.log_file == logfile
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
def test_parse_args_mutually_exclusive_args(sw, assets, capsys):
    cfgfile, _ = assets
    with raises(SystemExit) as e:
        experiment_manager.parse_args([sw.a, "SRW", sw.c, cfgfile, sw.q, sw.v])
    assert e.value.code == 1
    assert "Options --dry-run and --outfile may not be used together" in capsys.readouterr().err
