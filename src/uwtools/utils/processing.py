"""
Utilities for interacting with external processes.
"""

from pathlib import Path
from subprocess import STDOUT, CalledProcessError, check_output
from typing import Optional, Union

from uwtools.logging import INDENT, log


def execute(
    cmd: str,
    cwd: Optional[Union[Path, str]] = None,
    env: Optional[dict[str, str]] = None,
    log_output: Optional[bool] = False,
) -> tuple[bool, str]:
    """
    Execute a command in a subshell.

    :param cmd: The command to execute.
    :param cwd: Change to this directory before executing cmd.
    :param env: Environment variables to set before executing cmd.
    :param log_output: Log output from successful cmd? (Error output is always logged.)
    :return: A result object providing combined stder/stdout output and success values.
    """

    log.info("Executing: %s", cmd)
    if cwd:
        log.info("%sin %s", INDENT, cwd)
    if env:
        log.info("%swith environment variables:", INDENT)
        for key, val in env.items():
            log.info("%s%s=%s", INDENT * 2, key, val)
    try:
        output = check_output(
            cmd, cwd=cwd, encoding="utf=8", env=env, shell=True, stderr=STDOUT, text=True
        )
        logfunc = log.info
        success = True
    except CalledProcessError as e:
        output = e.output
        log.error("%sFailed with status: %s", INDENT, e.returncode)
        logfunc = log.error
        success = False
    if output and (log_output or not success):
        logfunc("%sOutput:", INDENT)
        for line in output.split("\n"):
            logfunc("%s%s", INDENT * 2, line)
    return success, output
