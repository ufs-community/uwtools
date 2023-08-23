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
    for fn in cfgfile, logfile:
        with open(fn, "w", encoding="utf-8"):
            pass
    return str(cfgfile), str(logfile)


def test_main(files):
    cfgfile, logfile = files
    args = ns(
        config_file=cfgfile,
        dry_run=True,
        log_file=logfile,
        forecast_model="FV3",
        outfile=None,
        quiet=False,
        verbose=False,
    )
    with patch.object(run_forecast, "parse_args", return_value=args):
        with patch.object(run_forecast.forecast, "FV3Forecast") as fv3fcst:
            with patch.object(run_forecast.cli_helpers, "setup_logging") as setuplogging:
                run_forecast.main()
                fv3fcst.assert_called_once_with(
                    config_file=args.config_file,
                    dry_run=True,
                    log=setuplogging(),
                    outfile=None,
                )
                # Test failure:
                fv3fcst().run.side_effect = run_forecast.UWConfigError
                with raises(SystemExit):
                    run_forecast.main()


@pytest.mark.parametrize("sw", [ns(c="-c"), ns(c="--config-file")])
def test_parse_args_bad_cfgfile(capsys, sw, tmp_path):
    """
    Fails if config file does not exist.
    """
    cfgfile = str(tmp_path / "no-such-file")
    with raises(FileNotFoundError):
        run_forecast.parse_args([sw.c, cfgfile])
    assert f"{cfgfile} does not exist" in capsys.readouterr().err


@pytest.mark.parametrize("noise", ["-q", "--quiet", "-v", "--verbose"])
@pytest.mark.parametrize("sw", [ns(c="-c", l="-l"), ns(c="--config-file", l="--log-file")])
def test_parse_args_good(sw, noise, files):
    """
    Test all valid CLI switch/value combinations.
    """
    cfgfile, logfile = files
    model = "FV3"  # representative (not exhaustive) choices
    parsed = run_forecast.parse_args(
        [
            sw.c,
            cfgfile,
            sw.l,
            logfile,
            "--forecast-model",
            model,
            noise,
        ]
    )
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
    assert parsed.forecast_model == model


@pytest.mark.parametrize("sw", [ns(q="-q", v="-v"), ns(q="--quiet", v="--verbose")])
def test_parse_args_mutually_exclusive_args(capsys, sw):
    with raises(SystemExit) as e:
        run_forecast.parse_args([sw.q, sw.v])
    assert e.value.code == 1
    assert "Options --dry-run and --outfile may not be used together" in capsys.readouterr().err
