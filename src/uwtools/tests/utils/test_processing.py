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
    result = processing.execute(cmd=cmd)
    assert "division by zero" in result.output
    assert result.success is False
    assert logged(caplog, "Executing: %s" % cmd)
    assert logged(caplog, "  Failed with status: 2")
    assert logged(caplog, "  Output:")
    assert logged(caplog, "    expr: division by zero")


def test_run_success(caplog, tmp_path):
    processing.log.setLevel(logging.INFO)
    cmd = "echo hello $FOO"
    assert processing.execute(cmd=cmd, cwd=tmp_path, env={"FOO": "bar"}, log_output=True)
    assert logged(caplog, "Executing: %s" % cmd)
    assert logged(caplog, "  in %s" % tmp_path)
    assert logged(caplog, "  with environment variables:")
    assert logged(caplog, "    FOO=bar")
    assert logged(caplog, "  Output:")
    assert logged(caplog, "    hello bar")
