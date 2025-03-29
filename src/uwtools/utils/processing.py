"""
Utilities for interacting with external processes.
"""

from pathlib import Path
from subprocess import STDOUT, CalledProcessError, check_output
from typing import Optional, Union

from uwtools.logging import INDENT, log


def run_shell_cmd(
    cmd: str,
    cwd: Optional[Union[Path, str]] = None,
    env: Optional[dict[str, str]] = None,
    log_output: Optional[bool] = False,
    taskname: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Run a command in a shell.

    :param cmd: The command to run.
    :param cwd: Change to this directory before running cmd.
    :param env: Environment variables to set before running cmd.
    :param log_output: Log output from successful cmd? (Error output is always logged.)
    :param taskname: Name of task executing this command, for logging.
    :return: A result object providing combined stder/stdout output and success values.
    """
    pre = f"{taskname}: " if taskname else ""
    msg = f"%sRunning: {cmd}"
    if cwd:
        msg += f" in {cwd}"
    if env:
        kvpairs = " ".join(f"{k}={v}" for k, v in env.items())
        msg += f" with environment variables {kvpairs}"
    log.info(msg, pre)
    try:
        output = check_output(
            cmd, cwd=cwd, encoding="utf=8", env=env, shell=True, stderr=STDOUT, text=True
        )
        logfunc = log.info
        success = True
    except CalledProcessError as e:
        output = e.output
        log.error("%sFailed with status: %s", pre, e.returncode)
        logfunc = log.error
        success = False
    if output and (log_output or not success):
        logfunc("%sOutput:", pre)
        for line in output.split("\n"):
            logfunc("%s%s%s", pre, INDENT, line)
    return success, output
