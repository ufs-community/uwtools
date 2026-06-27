"""
Tests for uwtools.utils.processing module.
"""

import logging
from subprocess import Popen
from textwrap import dedent
from unittest.mock import Mock

from pytest import mark

from uwtools.logging import log
from uwtools.utils import processing


def test_utils_processing_run_shell_cmd__callback():
    callback = Mock()
    success, output = processing.run_shell_cmd(cmd="echo callback_test", callback=callback)
    assert success
    assert "callback_test" in output
    callback.assert_called_once()
    assert isinstance(callback.call_args[0][0], Popen)


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
@mark.parametrize("taskname", ["test", None])
def test_utils_processing_run_shell_cmd__success(
    executable, log_output, quiet, taskname, tmp_path, uwcaplog
):
    cmd = "echo hello $FOO"
    if quiet:
        log.setLevel(logging.INFO)
    success, _ = processing.run_shell_cmd(
        cmd=cmd,
        cwd=tmp_path,
        env={"FOO": "bar"},
        log_output=log_output,
        taskname=taskname,
        quiet=quiet,
        executable=executable,
    )
    assert success
    if quiet:
        assert not uwcaplog.messages
    elif log_output:
        pre = f"[{taskname}] " if taskname else ""
        expected = """
        %sRunning: %s
          in directory
            %s
          with environment
            FOO=bar
        %sOutput:
        %s  hello bar
        """ % (pre, cmd, tmp_path, pre, pre)
        assert uwcaplog.text.strip() == dedent(expected).strip()
