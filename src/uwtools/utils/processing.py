"""
Utilities for interacting with external processes.
"""

from pathlib import Path
from subprocess import STDOUT, CalledProcessError, check_output
from typing import Dict, Optional, Tuple, Union

from uwtools.logging import log


def execute(
    cmd: str,
    cwd: Optional[Union[Path, str]] = None,
    env: Optional[Dict[str, str]] = None,
    log_output: Optional[bool] = False,
) -> Tuple[bool, str]:
    """
    Execute a command in a subshell.

    :param cmd: The command to execute.
    :param cwd: Change to this directory before executing cmd.
    :param env: Environment variables to set before executing cmd.
    :param log_output: Log output from successful cmd? (Error output is always logged.)
    :return: A result object providing combined stder/stdout output and success values.
    """

    indent = "  "
    log.info("Executing: %s", cmd)
    if cwd:
        log.info("%sin %s", indent, cwd)
    if env:
        log.info("%swith environment variables:", indent)
        for key, val in env.items():
            log.info("%s%s=%s", indent * 2, key, val)
    try:
        output = check_output(
            cmd, cwd=cwd, encoding="utf=8", env=env, shell=True, stderr=STDOUT, text=True
        )
        logfunc = log.info
        success = True
    except CalledProcessError as e:
        output = e.output
        log.error("%sFailed with status: %s", indent, e.returncode)
        logfunc = log.error
        success = False
    if output and (log_output or not success):
        logfunc("%sOutput:", indent)
        for line in output.split("\n"):
            logfunc("%s%s", indent * 2, line)
    return success, output
