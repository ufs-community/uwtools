"""
Support for HPC schedulers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Dict, List

from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.types import OptionalPath
from uwtools.utils.memory import Memory
from uwtools.utils.processing import execute


@dataclass(frozen=True)
class OptionalAttribs:
    """
    Keys for optional attributes.
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
class RequiredAttribs:
    """
    Keys for required attributes.
    """

    ACCOUNT: str = "account"
    WALLTIME: str = "walltime"


class JobScheduler(ABC):
    """
    An abstract class for interacting with HPC schedulers.
    """

    def __init__(self, props: Dict[str, Any]):
        self._props = props
        self._validate()

    # Public methods

    @property
    def directives(self) -> List[str]:
        """
        Returns resource-request scheduler directives.
        """
        pre, sep = self._prefix, self._directive_separator
        ds = []
        for key, value in self._pre_process().items():
            if key in self._attribs:
                switch = self._attribs[key]
                ds.append(
                    "%s%s%s" % (pre, sep, switch(value))
                    if callable(switch)
                    else "%s %s%s%s" % (pre, switch, sep, value)
                )
        return sorted(ds)

    @staticmethod
    def get_scheduler(props: Mapping) -> JobScheduler:
        """
        Returns a configured job scheduler.

        :param props: Configuration settings for job scheduling.
        :return: A configured job scheduler.
        :raises: UWConfigError if 'scheduler' is un- or mis-defined.
        """
        schedulers = {"slurm": Slurm, "pbs": PBS, "lsf": LSF}
        if name := props.get("scheduler"):
            log.debug("Getting '%s' scheduler", name)
            if scheduler_class := schedulers.get(name):
                return scheduler_class(props)  # type: ignore
            raise UWConfigError(
                "Scheduler '%s' should be one of: %s" % (name, ", ".join(schedulers.keys()))
            )
        raise UWConfigError(f"No 'scheduler' defined in {props}")

    def submit_job(self, runscript: Path, submit_file: OptionalPath = None) -> bool:
        """
        Submits a job to the scheduler.

        :param runscript: Path to the runscript.
        :param submit_file: File to write output of submit command to.
        :return: Did the run exit with a success status?
        """
        cmd = f"{self._submit_cmd} {runscript}"
        if submit_file:
            cmd += " 2>&1 | tee %s" % submit_file
        success, _ = execute(cmd=cmd, cwd=f"{runscript.parent}")
        return success

    # Private methods

    @property
    @abstractmethod
    def _attribs(self) -> Dict[str, Any]:
        """
        Returns a mapping from canonical names to scheduler-specific CLI switches.
        """

    @property
    @abstractmethod
    def _directive_separator(self) -> str:
        """
        Returns the character used to separate directive keys and values.
        """

    @property
    @abstractmethod
    def _prefix(self) -> str:
        """
        Returns the scheduler's resource-request prefix.
        """

    def _pre_process(self) -> Dict[str, Any]:
        """
        Pre-process attributes before converting to runscript.
        """
        return self._props

    @property
    @abstractmethod
    def _submit_cmd(self) -> str:
        """
        Returns the scheduler's job-submit executable name.
        """

    def _validate(self) -> None:
        """
        Validate configuration.

        :raises: UWConfigError if required props are missing.
        """
        if missing := [
            getattr(RequiredAttribs, x.name)
            for x in fields(RequiredAttribs)
            if getattr(RequiredAttribs, x.name) not in self._props
        ]:
            raise UWConfigError("Missing required attributes: %s" % ", ".join(missing))


class LSF(JobScheduler):
    """
    Represents a LSF based scheduler.
    """

    @property
    def _attribs(self) -> Dict[str, Any]:
        """
        Returns a mapping from canonical names to scheduler-specific CLI switches.
        """
        return {
            OptionalAttribs.JOB_NAME: "-J",
            OptionalAttribs.MEMORY: lambda x: f"-R rusage[mem={x}]",
            OptionalAttribs.NODES: lambda x: f"-n {x}",
            OptionalAttribs.QUEUE: "-q",
            OptionalAttribs.SHELL: "-L",
            OptionalAttribs.STDOUT: "-o",
            OptionalAttribs.TASKS_PER_NODE: lambda x: f"-R span[ptile={x}]",
            OptionalAttribs.THREADS: lambda x: f"-R affinity[core({x})]",
            RequiredAttribs.ACCOUNT: "-P",
            RequiredAttribs.WALLTIME: "-W",
        }

    @property
    def _directive_separator(self) -> str:
        """
        Returns the character used to separate directive keys and values.
        """
        return " "

    @property
    def _prefix(self) -> str:
        """
        Returns the scheduler's resource-request prefix.
        """
        return "#BSUB"

    def _pre_process(self) -> Dict[str, Any]:
        # LSF requires threads to be set (if None is provided, default to 1).
        props = self._props
        props[OptionalAttribs.THREADS] = props.get(OptionalAttribs.THREADS, 1)
        nodes = props.get(OptionalAttribs.NODES, "")
        tasks_per_node = props.get(OptionalAttribs.TASKS_PER_NODE, "")
        memory = props.get(OptionalAttribs.MEMORY, None)
        if memory is not None:
            mem_value = Memory(memory).convert("KB")
            props[self._attribs[OptionalAttribs.MEMORY](mem_value)] = ""
        props[OptionalAttribs.NODES] = int(tasks_per_node) * int(nodes)
        props.pop(OptionalAttribs.MEMORY, None)
        return props

    @property
    def _submit_cmd(self) -> str:
        """
        Returns the scheduler's job-submit executable name.
        """
        return "bsub"


class PBS(JobScheduler):
    """
    Represents the PBS scheduler.
    """

    @property
    def _attribs(self) -> Dict[str, Any]:
        """
        Returns a mapping from canonical names to scheduler-specific CLI switches.
        """
        return {
            OptionalAttribs.DEBUG: lambda x: f"-l debug={str(x).lower()}",
            OptionalAttribs.JOB_NAME: "-N",
            OptionalAttribs.MEMORY: "mem",
            OptionalAttribs.NODES: lambda x: f"-l select={x}",
            OptionalAttribs.QUEUE: "-q",
            OptionalAttribs.SHELL: "-S",
            OptionalAttribs.STDOUT: "-o",
            OptionalAttribs.TASKS_PER_NODE: "mpiprocs",
            OptionalAttribs.THREADS: "ompthreads",
            RequiredAttribs.ACCOUNT: "-A",
            RequiredAttribs.WALLTIME: "-l walltime=",
        }

    @property
    def _directive_separator(self) -> str:
        """
        Returns the character used to separate directive keys and values.
        """
        return " "

    @staticmethod
    def _placement(items: Dict[str, Any]) -> Dict[str, Any]:
        """
        Placement logic.
        """
        exclusive = items.get(OptionalAttribs.EXCLUSIVE)
        placement = items.get(OptionalAttribs.PLACEMENT)
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
        Returns the scheduler's resource-request prefix.
        """
        return "#PBS"

    def _pre_process(self) -> Dict[str, Any]:
        props = self._props
        props.update(self._select(props))
        props.update(self._placement(props))
        props.pop(OptionalAttribs.TASKS_PER_NODE, None)
        props.pop(OptionalAttribs.NODES, None)
        props.pop(OptionalAttribs.THREADS, None)
        props.pop(OptionalAttribs.MEMORY, None)
        props.pop("exclusive", None)
        props.pop("placement", None)
        props.pop("select", None)
        return dict(props)

    def _select(self, items: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select logic.
        """
        total_nodes = items.get(OptionalAttribs.NODES, "")
        tasks_per_node = items.get(OptionalAttribs.TASKS_PER_NODE, "")
        threads = items.get(OptionalAttribs.THREADS, 1)
        memory = items.get(OptionalAttribs.MEMORY, "")
        select = [
            f"{total_nodes}",
            f"{self._attribs[OptionalAttribs.TASKS_PER_NODE]}={tasks_per_node}",
            f"{self._attribs[OptionalAttribs.THREADS]}={threads}",
            f"ncpus={int(tasks_per_node) * int(threads)}",
        ]
        if memory:
            select.append(f"{self._attribs[OptionalAttribs.MEMORY]}={memory}")
        items["-l select="] = ":".join(select)
        return items

    @property
    def _submit_cmd(self) -> str:
        """
        Returns the scheduler's job-submit executable name.
        """
        return "qsub"


class Slurm(JobScheduler):
    """
    Represents the Slurm scheduler.
    """

    @property
    def _attribs(self) -> Dict[str, Any]:
        """
        Returns a mapping from canonical names to scheduler-specific CLI switches.
        """
        return {
            OptionalAttribs.CORES: "--ntasks",
            OptionalAttribs.EXCLUSIVE: lambda _: "--exclusive",
            OptionalAttribs.EXPORT: "--export",
            OptionalAttribs.JOB_NAME: "--job-name",
            OptionalAttribs.MEMORY: "--mem",
            OptionalAttribs.NODES: "--nodes",
            OptionalAttribs.PARTITION: "--partition",
            OptionalAttribs.QUEUE: "--qos",
            OptionalAttribs.RUNDIR: "--chdir",
            OptionalAttribs.STDERR: "--error",
            OptionalAttribs.STDOUT: "--output",
            OptionalAttribs.TASKS_PER_NODE: "--ntasks-per-node",
            OptionalAttribs.THREADS: "--cpus-per-task",
            RequiredAttribs.ACCOUNT: "--account",
            RequiredAttribs.WALLTIME: "--time",
        }

    @property
    def _directive_separator(self) -> str:
        """
        Returns the character used to separate directive keys and values.
        """
        return "="

    @property
    def _prefix(self) -> str:
        """
        Returns the scheduler's resource-request prefix.
        """
        return "#SBATCH"

    @property
    def _submit_cmd(self) -> str:
        """
        Returns the scheduler's job-submit executable name.
        """
        return "sbatch"
