# pylint: disable=duplicate-code,missing-function-docstring,redefined-outer-name
"""
Tests for the run-forecast CLI.
"""

import logging
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
    machinefile = tmp_path / "machine.yaml"
    for path in cfgfile, machinefile:
        path.touch()
    return str(cfgfile), str(machinefile)


def test_main(files):
    cfgfile, machinefile = files
    args = ns(
        config_file=cfgfile,
        forecast_model="FV3",
        machine=machinefile,
        quiet=False,
        verbose=False,
    )
    with patch.object(run_forecast, "parse_args", return_value=args):
        with patch.object(run_forecast.forecast, "FV3Forecast") as fv3fcst:
            run_forecast.main()
            fv3fcst.assert_called_once_with(cfgfile, machinefile)


@pytest.mark.parametrize("sw", [ns(c="-c"), ns(c="--config-file")])
def test_parse_args_bad_cfgfile(capsys, sw, tmp_path):
    """
    Fails if config file does not exist.
    """
    logging.getLogger().setLevel(logging.INFO)
    cfgfile = str(tmp_path / "no-such-file")
    with raises(FileNotFoundError):
        run_forecast.parse_args([sw.c, cfgfile])
    assert f"{cfgfile} does not exist" in capsys.readouterr().err


@pytest.mark.parametrize("sw", [ns(m="-m"), ns(m="--machine")])
def test_parse_args_bad_machinefile(capsys, sw, tmp_path):
    """
    Fails if machine file does not exist.
    """
    logging.getLogger().setLevel(logging.INFO)
    machinefile = str(tmp_path / "no-such-file")
    with raises(FileNotFoundError):
        run_forecast.parse_args([sw.m, machinefile])
    assert f"{machinefile} does not exist" in capsys.readouterr().err


@pytest.mark.parametrize("noise", ["-q", "--quiet", "-v", "--verbose"])
@pytest.mark.parametrize("sw", [ns(c="-c", m="-m"), ns(c="--config-file", m="--machine")])
def test_parse_args_good(files, noise, sw):
    """
    Test all valid CLI switch/value combinations.
    """
    cfgfile, machinefile = files
    app, model = "SRW", "FV3"  # representative (not exhaustive) choices
    parsed = run_forecast.parse_args(
        [
            sw.c,
            cfgfile,
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
def test_parse_args_mutually_exclusive_args(capsys, sw):
    with raises(SystemExit) as e:
        run_forecast.parse_args([sw.q, sw.v])
    assert e.value.code == 1
    assert "Options --dry-run and --outfile may not be used together" in capsys.readouterr().err
