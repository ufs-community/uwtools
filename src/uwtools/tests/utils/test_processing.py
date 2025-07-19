"""
Tests for uwtools.utils.processing module.
"""

import logging

from pytest import mark

from uwtools.logging import log
from uwtools.utils import processing


def test_utils_processing_run_shell_cmd__failure(logged):
    cmd = "expr 1 / 0"
    success, output = processing.run_shell_cmd(cmd=cmd)
    assert "division by zero" in output
    assert success is False
    assert logged("Running: %s" % cmd)
    assert logged("Failed with status: 2")
    assert logged("Output:")
    assert logged("  expr: division by zero")


@mark.parametrize("quiet", [True, False])
def test_utils_processing_run_shell_cmd__success(caplog, logged, quiet, tmp_path):
    cmd = "echo hello $FOO"
    if quiet:
        log.setLevel(logging.INFO)
    success, _ = processing.run_shell_cmd(
        cmd=cmd, cwd=tmp_path, env={"FOO": "bar"}, log_output=True, quiet=quiet
    )
    assert success
    if quiet:
        assert not caplog.messages
    else:
        assert logged(f"Running: {cmd} in {tmp_path} with environment variables FOO=bar")
        assert logged("Output:")
        assert logged("  hello bar")
