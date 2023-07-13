# pylint: disable=duplicate-code,missing-function-docstring,redefined-outer-name
"""
Tests for the run-forecast CLI.
"""

from types import SimpleNamespace as ns
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from uwtools.cli import run_forecast

# NB: Ensure that at least one test exercises both short and long forms of each
#     CLI switch.


@fixture
def files(tmp_path):
    cfgfile = tmp_path / "cfg.yaml"
    logfile = tmp_path / "log"
    machinefile = tmp_path / "machine.yaml"
    for fn in cfgfile, logfile, machinefile:
        with open(fn, "w", encoding="utf-8"):
            pass
    return str(cfgfile), str(logfile), str(machinefile)


def test_main(files):
    cfgfile, logfile, machinefile = files
    args = ns(
        config_file=cfgfile,
        forecast_model="FV3",
        log_file=logfile,
        machine=machinefile,
        quiet=False,
        verbose=False,
    )
    with patch.object(run_forecast, "parse_args", return_value=args):
        with patch.object(run_forecast.forecast, "FV3Forecast") as fv3fcst:
            run_forecast.main()
            fv3fcst.assert_called_once_with(cfgfile, machinefile, log_name="run-forecast")


@pytest.mark.parametrize("sw", [ns(c="-c"), ns(c="--config-file")])
def test_parse_args_bad_cfgfile(sw, tmp_path, capsys):
    """
    Fails if config file does not exist.
    """
    cfgfile = str(tmp_path / "no-such-file")
    with raises(SystemExit) as e:
        run_forecast.parse_args([sw.c, cfgfile])
    assert e.value.code == 2
    assert "does not exist!" in capsys.readouterr().err


@pytest.mark.parametrize("sw", [ns(m="-m"), ns(m="--machine")])
def test_parse_args_bad_machinefile(sw, tmp_path, capsys):
    """
    Fails if machine file does not exist.
    """
    machinefile = str(tmp_path / "no-such-file")
    with raises(SystemExit) as e:
        run_forecast.parse_args([sw.m, machinefile])
    assert e.value.code == 2
    assert "does not exist!" in capsys.readouterr().err


@pytest.mark.parametrize("noise", ["-q", "--quiet", "-v", "--verbose"])
@pytest.mark.parametrize(
    "sw", [ns(c="-c", l="-l", m="-m"), ns(c="--config-file", l="--log-file", m="--machine")]
)
def test_parse_args_good(sw, noise, files):
    """
    Test all valid CLI switch/value combinations.
    """
    cfgfile, machinefile, logfile = files
    app, model = "SRW", "FV3"  # representative (not exhaustive) choices
    parsed = run_forecast.parse_args(
        [
            sw.c,
            cfgfile,
            sw.l,
            logfile,
            sw.m,
            machinefile,
            "--forecast-app",
            app,
            "--forecast-model",
            model,
            noise,
        ]
    )
    assert parsed.config_file == cfgfile
    assert parsed.log_file == logfile
    assert parsed.machine == machinefile
    if noise in ["-q", "--quiet"]:
        sw_off = parsed.verbose
        sw_on = parsed.quiet
    else:
        sw_off = parsed.quiet
        sw_on = parsed.verbose
    assert sw_off is False
    assert sw_on is True
    assert parsed.forecast_app == app
    assert parsed.forecast_model == model


@pytest.mark.parametrize("sw", [ns(q="-q", v="-v"), ns(q="--quiet", v="--verbose")])
def test_parse_args_mutually_exclusive_args(sw, capsys):
    with raises(SystemExit) as e:
        run_forecast.parse_args([sw.q, sw.v])
    assert e.value.code == 1
    assert "Options --dry-run and --outfile may not be used together" in capsys.readouterr().err
