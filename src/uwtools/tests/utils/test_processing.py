# pylint: disable=missing-function-docstring
"""
Tests for uwtools.utils.processing module.
"""

import logging

from uwtools.tests.support import logged
from uwtools.utils import processing


def test_run_failure(caplog):
    processing.log.setLevel(logging.INFO)
    cmd = "expr 1 / 0"
    success, output = processing.run_shell_cmd(cmd=cmd)
    assert "division by zero" in output
    assert success is False
    assert logged(caplog, "Running: %s" % cmd)
    assert logged(caplog, "Failed with status: 2")
    assert logged(caplog, "Output:")
    assert logged(caplog, "  expr: division by zero")


def test_run_success(caplog, tmp_path):
    processing.log.setLevel(logging.INFO)
    cmd = "echo hello $FOO"
    success, _ = processing.run_shell_cmd(
        cmd=cmd, cwd=tmp_path, env={"FOO": "bar"}, log_output=True
    )
    assert success
    assert logged(caplog, f"Running: {cmd} in {tmp_path} with environment variables FOO=bar")
    assert logged(caplog, "Output:")
    assert logged(caplog, "  hello bar")
