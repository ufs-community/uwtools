"""
Utilities for interacting with external processes.
"""

from __future__ import annotations

from subprocess import STDOUT, CalledProcessError, check_output
from typing import TYPE_CHECKING

from uwtools.logging import INDENT, log

if TYPE_CHECKING:
    from pathlib import Path


def run_shell_cmd(
    cmd: str,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    log_output: bool | None = False,
    taskname: str | None = None,
    quiet: bool | None = None,
) -> tuple[bool, str]:
    """
    Run a command in a shell.

    :param cmd: The command to run.
    :param cwd: Change to this directory before running cmd.
    :param env: Environment variables to set before running cmd.
    :param log_output: Log output from successful cmd? (Error output is always logged.)
    :param taskname: Name of task executing this command, for logging.
    :param quiet: Log INFO messages as DEBUG.
    :return: A result object providing combined stder/stdout output and success values.
    """
    pre = f"{taskname}: " if taskname else ""
    msg = f"%sRunning: {cmd}"
    if cwd:
        msg += f" in {cwd}"
    if env:
        kvpairs = " ".join(f"{k}={v}" for k, v in env.items())
        msg += f" with environment variables {kvpairs}"
    logfunc = log.debug if quiet else log.info
    logfunc(msg, pre)
    try:
        output = check_output(
            cmd, cwd=cwd, encoding="utf=8", env=env, shell=True, stderr=STDOUT, text=True
        )
        success = True
    except CalledProcessError as e:
        output = e.output
        log.error("%sFailed with status: %s", pre, e.returncode)
        logfunc = log.error
        success = False
    if output and (log_output or not success):
        logfunc("%sOutput:", pre)
        for line in output.strip().split("\n"):
            logfunc("%s%s%s", pre, INDENT, line)
    return success, output
