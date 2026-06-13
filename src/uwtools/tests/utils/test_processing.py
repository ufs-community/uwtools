"""
Tests for uwtools.utils.processing module.
"""

import logging

from pytest import mark

from uwtools.logging import log
from uwtools.utils import processing


@mark.parametrize("quiet", [True, False])
def test_utils_processing_run_shell_cmd__failure(caplog, logged, quiet):
    caplog.set_level(logging.INFO if quiet else logging.DEBUG)
    cmd = "expr 1 / 0"
    success, output = processing.run_shell_cmd(cmd=cmd, quiet=quiet)
    assert "division by zero" in output
    assert success is False
    check = lambda msg: not logged(msg) if quiet else logged
    assert check("Running:")
    assert check("  %s" % cmd)
    assert check("Failed with status: 2")
    assert check("Output:")
    assert check("  expr: division by zero")


@mark.parametrize("executable", ["/bin/bash", None])
@mark.parametrize("log_output", [True, False])
@mark.parametrize("quiet", [True, False])
def test_utils_processing_run_shell_cmd__success(
    caplog, executable, logged, log_output, quiet, tmp_path
):
    cmd = "echo hello $FOO"
    if quiet:
        log.setLevel(logging.INFO)
    success, _ = processing.run_shell_cmd(
        cmd=cmd,
        cwd=tmp_path,
        env={"FOO": "bar"},
        log_output=log_output,
        quiet=quiet,
        executable=executable,
    )
    assert success
    if quiet:
        assert not caplog.messages
    elif log_output:
        assert logged("Running in %s with environment variables FOO=bar:" % tmp_path)
        assert logged("  %s" % cmd)
        assert logged("Output:")
        assert logged("  hello bar")
