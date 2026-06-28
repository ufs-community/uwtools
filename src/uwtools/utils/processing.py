"""
Utilities for interacting with external processes.
"""

from __future__ import annotations

from subprocess import PIPE, STDOUT, Popen
from typing import TYPE_CHECKING

from uwtools.logging import INDENT, log

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def run_shell_cmd(
    cmd: str,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    log_output: bool | None = False,
    taskname: str | None = None,
    quiet: bool | None = None,
    callback: Callable[[Popen], None] | None = None,
    executable: str | None = None,
) -> tuple[bool, str]:
    """
    Run a command in a shell.

    :param cmd: The command to run.
    :param cwd: Change to this directory before running cmd.
    :param env: Environment variables to set before running cmd.
    :param log_output: Log output from successful cmd? (Error output is always logged.)
    :param taskname: Name of task executing this command, for logging.
    :param quiet: Log INFO messages as DEBUG.
    :param executable: Interpreter to use (e.g. "/bin/bash")
    :param callback: Optional callable, called with the Popen process object.
    :return: A result object providing combined stder/stdout output and success values.
    """
    pre = f"[{taskname}] " if taskname else ""
    logfunc = log.debug if quiet else log.info
    logfunc("%sRunning: %s", pre, cmd)
    if cwd:
        logfunc("  in directory")
        logfunc("    %s", cwd)
    if env:
        logfunc("  with environment")
        for k in sorted(env):
            logfunc("    %s=%s", k, env[k])
    kwargs: dict = dict(  # noqa: S604
        cwd=cwd,
        encoding="utf=8",
        env=env,
        shell=True,
        start_new_session=True,
        stderr=STDOUT,
        stdout=PIPE,
        text=True,
    )
    if executable:
        kwargs["executable"] = executable
    proc = Popen(cmd, **kwargs)  # noqa: S603
    if callback:
        callback(proc)
    output, _ = proc.communicate()
    if proc.returncode == 0:
        success = True
    else:
        if not quiet:
            log.error("%sFailed with status: %s", pre, proc.returncode)
            logfunc = log.error
        success = False
    if output and (log_output or not success):
        logfunc("%sOutput:", pre)
        for line in output.strip().split("\n"):
            logfunc("%s%s%s", pre, INDENT, line)
    return success, output
