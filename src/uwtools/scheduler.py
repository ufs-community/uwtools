"""
Support for HPC schedulers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Any

from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.strings import STR
from uwtools.utils.processing import run_shell_cmd

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


class JobScheduler(ABC):
    """
    An abstract class for interacting with HPC schedulers.
    """

    def __init__(self, props: dict[str, Any]):
        self._scheduler = props[STR.scheduler]
        self._props = {k: v for k, v in props.items() if k != STR.scheduler}
        self._validate_props()

    # Public methods

    @property
    def directives_and_initcmds(self) -> tuple[list[str], list[str]]:
        """
        The resource-request scheduler directives and any additional setup commands.
        """
        pre, sep = self._prefix, self._directive_separator
        ds = []
        for key, value in self._processed_props.items():
            if key in self._forbidden_directives:
                msg = "Directive '%s' invalid for scheduler '%s'"
                raise UWConfigError(msg % (key, self._scheduler))
            if key in self._managed_directives:
                switch = self._managed_directives[key]
                if callable(switch) and (x := switch(value)) is not None:
                    ds.append("%s %s" % (pre, x))
                else:
                    x = "" if switch.endswith("=") else sep
                    ds.append("%s %s%s%s" % (pre, switch, x, value))
            else:
                x = "" if key.endswith("=") else sep
                ds.append("%s %s%s%s" % (pre, key, x, value))
        return sorted(ds), self._initcmds

    @staticmethod
    def get_scheduler(props: Mapping) -> JobScheduler:
        """
        Return a configured job scheduler.

        :param props: Configuration settings for job scheduler.
        :return: A configured job scheduler.
        :raises: UWConfigError if 'scheduler' is un- or mis-defined.
        """
        schedulers = {"slurm": Slurm, "pbs": PBS, "lsf": LSF}
        if name := props.get(STR.scheduler):
            log.debug("Getting '%s' scheduler", name)
            if scheduler_class := schedulers.get(name):
                return scheduler_class(props)  # type: ignore[abstract,arg-type]
            msg = "Scheduler '%s' should be one of: %s" % (name, ", ".join(schedulers.keys()))
            raise UWConfigError(msg)
        msg = f"No 'scheduler' defined in {props}"
        raise UWConfigError(msg)

    def submit_job(self, runscript: Path, submit_file: Path | None = None) -> bool:
        """
        Submit a job to the scheduler.

        :param runscript: Path to the runscript.
        :param submit_file: Path to file to write output of submit command to.
        :return: Did the run exit with a success status?
        """
        cmd = f"{self._submit_cmd} {runscript}"
        if submit_file:
            cmd += " 2>&1 | tee %s" % submit_file
        success, _ = run_shell_cmd(cmd=cmd, cwd=f"{runscript.parent}")
        return success

    # Private methods

    @property
    @abstractmethod
    def _directive_separator(self) -> str:
        """
        The character used to separate directive keys and values.
        """

    @property
    def _initcmds(self) -> list[str]:
        """
        Additional initialization commands a batch job must run.
        """
        return []

    @property
    @abstractmethod
    def _forbidden_directives(self) -> list[str]:
        """
        The directives that this scheduler does not support.
        """

    @property
    @abstractmethod
    def _managed_directives(self) -> dict[str, Any]:
        """
        A mapping from canonical names to scheduler-specific CLI switches.
        """

    @property
    @abstractmethod
    def _prefix(self) -> str:
        """
        The scheduler's resource-request prefix.
        """

    @property
    def _processed_props(self) -> dict[str, Any]:
        """
        Pre-processed runscript directives.
        """
        return self._props

    @property
    @abstractmethod
    def _submit_cmd(self) -> str:
        """
        The scheduler's job-submit executable name.
        """

    def _validate_props(self) -> None:
        """
        Validate scheduler-configuration properties.

        :raises: UWConfigError if required props are missing.
        """
        if missing := [
            getattr(_DirectivesRequired, x.name)
            for x in fields(_DirectivesRequired)
            if getattr(_DirectivesRequired, x.name) not in self._props
        ]:
            msg = "Missing required directives: %s" % ", ".join(missing)
            raise UWConfigError(msg)


class LSF(JobScheduler):
    """
    Represents a LSF based scheduler.
    """

    @property
    def _directive_separator(self) -> str:
        """
        The character used to separate directive keys and values.
        """
        return " "

    @property
    def _forbidden_directives(self) -> list[str]:
        """
        Directives that this scheduler does not support.
        """
        return []

    @property
    def _managed_directives(self) -> dict[str, Any]:
        """
        A mapping from canonical names to scheduler-specific CLI switches.
        """
        return {
            _DirectivesOptional.JOB_NAME: "-J",
            _DirectivesOptional.MEMORY: lambda x: f"-R rusage[mem={x}]",
            _DirectivesOptional.NODES: lambda x: f"-n {x}",
            _DirectivesOptional.QUEUE: "-q",
            _DirectivesOptional.SHELL: "-L",
            _DirectivesOptional.STDOUT: "-o",
            _DirectivesOptional.TASKS_PER_NODE: lambda x: f"-R span[ptile={x}]",
            _DirectivesOptional.THREADS: lambda x: f"-R affinity[core({x})]",
            _DirectivesRequired.ACCOUNT: "-P",
            _DirectivesRequired.WALLTIME: "-W",
        }

    @property
    def _prefix(self) -> str:
        """
        The scheduler's resource-request prefix.
        """
        return "#BSUB"

    @property
    def _processed_props(self) -> dict[str, Any]:
        """
        Pre-processed runscript directives.
        """
        props = deepcopy(self._props)
        props[_DirectivesOptional.THREADS] = props.get(_DirectivesOptional.THREADS, 1)
        return props

    @property
    def _submit_cmd(self) -> str:
        """
        The scheduler's job-submit executable name.
        """
        return "bsub"


class PBS(JobScheduler):
    """
    Represents the PBS scheduler.
    """

    @property
    def _directive_separator(self) -> str:
        """
        The character used to separate directive keys and values.
        """
        return " "

    @property
    def _forbidden_directives(self) -> list[str]:
        """
        Directives that this scheduler does not support.
        """
        return [_DirectivesOptional.RUNDIR]

    @property
    def _initcmds(self) -> list[str]:
        """
        Additional initialization commands a PBS batch job must run.
        """
        if rundir := self._props.get(_DirectivesOptional.RUNDIR):
            return [f"cd {rundir}"]
        return []

    @property
    def _managed_directives(self) -> dict[str, Any]:
        """
        A mapping from canonical names to scheduler-specific CLI switches.
        """
        return {
            _DirectivesOptional.DEBUG: lambda x: f"-l debug={str(x).lower()}",
            _DirectivesOptional.JOB_NAME: "-N",
            _DirectivesOptional.MEMORY: "mem",
            _DirectivesOptional.NODES: lambda x: f"-l select={x}",
            _DirectivesOptional.QUEUE: "-q",
            _DirectivesOptional.SHELL: "-S",
            _DirectivesOptional.STDOUT: "-o",
            _DirectivesOptional.TASKS_PER_NODE: "mpiprocs",
            _DirectivesOptional.THREADS: "ompthreads",
            _DirectivesRequired.ACCOUNT: "-A",
            _DirectivesRequired.WALLTIME: "-l walltime=",
        }

    @staticmethod
    def _placement(items: dict[str, Any]) -> dict[str, Any]:
        """
        Return provided items with scheduler-specific replacements.
        """
        exclusive = items.get(_DirectivesOptional.EXCLUSIVE)
        placement = items.get(_DirectivesOptional.PLACEMENT)
        if not exclusive and not placement:
            return items
        output = []
        if placement:
            output.append(str(placement))
        if exclusive:
            output.append("excl")
        if len(output) > 0:
            items["-l place="] = ":".join(output)
        return items

    @property
    def _prefix(self) -> str:
        """
        The scheduler's resource-request prefix.
        """
        return "#PBS"

    @property
    def _processed_props(self) -> dict[str, Any]:
        """
        Pre-processed runscript directives.
        """
        props = self._props
        props.update(self._select(props))
        props.update(self._placement(props))
        props.pop(_DirectivesOptional.TASKS_PER_NODE, None)
        props.pop(_DirectivesOptional.NODES, None)
        props.pop(_DirectivesOptional.RUNDIR, None)
        props.pop(_DirectivesOptional.THREADS, None)
        props.pop(_DirectivesOptional.MEMORY, None)
        props.pop("exclusive", None)
        props.pop("placement", None)
        props.pop("select", None)
        return dict(props)

    def _select(self, items: dict[str, Any]) -> dict[str, Any]:
        """
        Return provided items with scheduler-specific selections.
        """
        select = []
        if nodes := items.get(_DirectivesOptional.NODES):
            select.append(str(nodes))
        if tasks_per_node := items.get(_DirectivesOptional.TASKS_PER_NODE):
            select.append(
                f"{self._managed_directives[_DirectivesOptional.TASKS_PER_NODE]}={tasks_per_node}"
            )
        threads = items.get(_DirectivesOptional.THREADS, 1)
        select.append(f"{self._managed_directives[_DirectivesOptional.THREADS]}={threads}")
        if tasks_per_node:
            select.append(f"ncpus={int(tasks_per_node) * int(threads)}")
        if memory := items.get(_DirectivesOptional.MEMORY):
            select.append(f"{self._managed_directives[_DirectivesOptional.MEMORY]}={memory}")
        items["-l select="] = ":".join(select)
        return items

    @property
    def _submit_cmd(self) -> str:
        """
        The scheduler's job-submit executable name.
        """
        return "qsub"


class Slurm(JobScheduler):
    """
    Represents the Slurm scheduler.
    """

    @property
    def _forbidden_directives(self) -> list[str]:
        """
        Directives that this scheduler does not support.
        """
        return [_DirectivesOptional.SHELL]

    @property
    def _managed_directives(self) -> dict[str, Any]:
        """
        A mapping from canonical names to scheduler-specific CLI switches.
        """
        return {
            _DirectivesOptional.CORES: "--ntasks",
            _DirectivesOptional.DEBUG: lambda b: "--verbose" if b else None,
            _DirectivesOptional.EXCLUSIVE: lambda b: "--exclusive" if b else None,
            _DirectivesOptional.EXPORT: "--export",
            _DirectivesOptional.JOB_NAME: "--job-name",
            _DirectivesOptional.MEMORY: "--mem",
            _DirectivesOptional.NODES: "--nodes",
            _DirectivesOptional.PARTITION: "--partition",
            _DirectivesOptional.QUEUE: "--qos",
            _DirectivesOptional.RUNDIR: "--chdir",
            _DirectivesOptional.STDERR: "--error",
            _DirectivesOptional.STDOUT: "--output",
            _DirectivesOptional.TASKS_PER_NODE: "--ntasks-per-node",
            _DirectivesOptional.THREADS: "--cpus-per-task",
            _DirectivesRequired.ACCOUNT: "--account",
            _DirectivesRequired.WALLTIME: "--time",
        }

    @property
    def _directive_separator(self) -> str:
        """
        The character used to separate directive keys and values.
        """
        return "="

    @property
    def _prefix(self) -> str:
        """
        The scheduler's resource-request prefix.
        """
        return "#SBATCH"

    @property
    def _submit_cmd(self) -> str:
        """
        The scheduler's job-submit executable name.
        """
        return "sbatch"


@dataclass(frozen=True)
class _DirectivesOptional:
    """
    Keys for optional directives.
    """

    CORES: str = "cores"
    DEBUG: str = "debug"
    EXCLUSIVE: str = "exclusive"
    EXPORT: str = "export"
    JOB_NAME: str = "jobname"
    MEMORY: str = "memory"
    NODES: str = "nodes"
    PARTITION: str = "partition"
    PLACEMENT: str = "placement"
    QUEUE: str = "queue"
    RUNDIR: str = "rundir"
    SHELL: str = "shell"
    STDERR: str = "stderr"
    STDOUT: str = "stdout"
    TASKS_PER_NODE: str = "tasks_per_node"
    THREADS: str = "threads"


@dataclass(frozen=True)
class _DirectivesRequired:
    """
    Keys for required directives.
    """

    ACCOUNT: str = "account"
    WALLTIME: str = "walltime"
