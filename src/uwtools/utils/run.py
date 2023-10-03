"""
Helpers for executing processes in subshells.
"""

import logging
from pathlib import Path
from subprocess import STDOUT, CalledProcessError, check_output
from types import SimpleNamespace as ns
from typing import Dict, Optional, Union


def run(
    cmd: str,
    cwd: Optional[Union[Path, str]] = None,
    env: Optional[Dict[str, str]] = None,
    log: Optional[bool] = False,
) -> ns:
    """
    Run a command in a subshell.

    :param cmd: The command to run.
    :param cwd: Change to this directory before running cmd.
    :param env: Environment variables to set before running cmd.
    :param log: Log output from successful cmd? (Error output is always logged.)
    :return: A result object providing combined stder/stdout output and success values.
    """

    indent = "  "
    logging.info("Running: %s", cmd)
    if cwd:
        logging.info("%sin %s", indent, cwd)
    if env:
        logging.info("%swith environment variables:", indent)
        for key, val in env.items():
            logging.info("%s%s=%s", indent * 2, key, val)
    try:
        output = check_output(
            cmd, cwd=cwd, encoding="utf=8", env=env, shell=True, stderr=STDOUT, text=True
        )
        logfunc = logging.info
        success = True
    except CalledProcessError as e:
        output = e.output
        logging.error("%sFailed with status: %s", indent, e.returncode)
        logfunc = logging.error
        success = False
    if output and (log or not success):
        logfunc("%sOutput:", indent)
        for line in output.split("\n"):
            logfunc("%s%s", indent * 2, line)
    return ns(output=output, success=success)
