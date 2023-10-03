"""
Tests for uwtools.utils.run module.
"""

from uwtools.utils import run
from uwtools.tests.support import logged

def test_run_failure(caplog):
    run.logging.getLogger().setLevel(run.logging.INFO)
    cmd = "expr 1 / 0"
    result = run.run(cmd=cmd)
    assert "division by zero" in result.output
    assert result.success is False
    assert logged(caplog, "Running: %s" % cmd)
    assert logged(caplog, "  Failed with status: 2")
    assert logged(caplog, "  Output:")
    assert logged(caplog, "    expr: division by zero")


def test_run_success(caplog, tmp_path):
    run.logging.getLogger().setLevel(run.logging.INFO)
    cmd = "echo hello $FOO"
    assert run.run(cmd=cmd, cwd=tmp_path, env={"FOO": "bar"}, log=True)
    assert logged(caplog, "Running: %s" % cmd)
    assert logged(caplog, "  in %s" % tmp_path)
    assert logged(caplog, "  with environment variables:")
    assert logged(caplog, "    FOO=bar")
    assert logged(caplog, "  Output:")
    assert logged(caplog, "    hello bar")
