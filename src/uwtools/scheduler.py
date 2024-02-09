"""
Job Scheduling.
"""

from __future__ import annotations

import re
from collections import UserDict
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Dict

from uwtools.exceptions import UWConfigError
from uwtools.logging import log
from uwtools.types import OptionalPath
from uwtools.utils.memory import Memory
from uwtools.utils.processing import execute


class RequiredAttribs:
    """
    Key for required attributes.
    """

    ACCOUNT = "account"
    QUEUE = "queue"
    WALLTIME = "walltime"


class OptionalAttribs:
    """
    Key for optional attributes.
    """

    CORES = "cores"
    DEBUG = "debug"
    EXCLUSIVE = "exclusive"
    EXPORT = "export"
    JOB_NAME = "jobname"
    MEMORY = "memory"
    NODES = "nodes"
    PARTITION = "partition"
    PLACEMENT = "placement"
    RUNDIR = "rundir"
    SHELL = "shell"
    STDERR = "stderr"
    STDOUT = "stdout"
    TASKS_PER_NODE = "tasks_per_node"
    THREADS = "threads"


class JobScheduler(UserDict):
    """
    A class for interacting with HPC schedulers.
    """

    attrib_map: dict = {}
    prefix = ""
    key_value_separator = "="

    def __init__(self, props):
        super().__init__(props)
        self.validate_props(props)

    def __getattr__(self, name) -> Any:
        if name in self:
            return self[name]
        raise AttributeError(name)

    @property
    def directives(self):
        """
        ???
        """
        sanitized_attribs = self.pre_process()
        known = []
        for key, value in sanitized_attribs.items():
            if key in self.attrib_map:
                scheduler_flag = (
                    self.attrib_map[key](value)
                    if callable(self.attrib_map[key])
                    else self.attrib_map[key]
                )
                scheduler_value = "" if callable(self.attrib_map[key]) else value
                key_value_separator = (
                    "" if callable(self.attrib_map[key]) else self.key_value_separator
                )
                directive = f"{self.prefix} {scheduler_flag}{key_value_separator}{scheduler_value}"
                known.append(directive.strip())
        unknown = [
            f"{self.prefix} {key}{self.key_value_separator}{value}".strip()
            for (key, value) in sanitized_attribs.items()
            if key not in self.attrib_map and value
        ]
        flags = [
            f"{self.prefix} {key}".strip()
            for (key, value) in sanitized_attribs.items()
            if not value
        ]
        return [re.sub(r"\s{0,}\=\s{0,}", "=", x) for x in known + unknown + flags]

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
                return scheduler_class(props)
            raise UWConfigError(
                "Scheduler '%s' should be one of: %s" % (name, ", ".join(schedulers.keys()))
            )
        raise UWConfigError(f"No 'scheduler' defined in {props}")

    def pre_process(self) -> Dict[str, Any]:
        """
        Pre-process attributes before converting to runscript.
        """
        return self.data

    def submit_job(self, runscript: Path, submit_file: OptionalPath = None) -> bool:
        """
        Submits a job to the scheduler.

        :param runscript: Path to the runscript.
        :param submit_file: File to write output of submit command to.
        :return: Did the run exit with a success status?
        """
        cmd = f"{self.submit_command} {runscript}"
        if submit_file:
            cmd += " 2>&1 | tee %s" % submit_file
        success, _ = execute(cmd=cmd, cwd=f"{runscript.parent}")
        return success

    @staticmethod
    def validate_props(props) -> None:
        """
        Raises ValueError if invalid.
        """
        members = [
            getattr(RequiredAttribs, attr)
            for attr in dir(RequiredAttribs)
            if not callable(getattr(RequiredAttribs, attr)) and not attr.startswith("__")
        ]
        if diff := [x for x in members if x not in props]:
            raise ValueError(f"Missing required attributes: [{', '.join(diff)}]")


class Slurm(JobScheduler):
    """
    Represents a Slurm based scheduler.
    """

    prefix = "#SBATCH"
    submit_command = "sbatch"

    attrib_map = {
        OptionalAttribs.CORES: "--ntasks",
        OptionalAttribs.EXCLUSIVE: lambda _: "--exclusive",
        OptionalAttribs.EXPORT: "--export",
        OptionalAttribs.JOB_NAME: "--job-name",
        OptionalAttribs.MEMORY: "--mem",
        OptionalAttribs.NODES: "--nodes",
        OptionalAttribs.PARTITION: "--partition",
        OptionalAttribs.RUNDIR: "--chdir",
        OptionalAttribs.STDERR: "--error",
        OptionalAttribs.STDOUT: "--output",
        OptionalAttribs.TASKS_PER_NODE: "--ntasks-per-node",
        OptionalAttribs.THREADS: "--cpus-per-task",
        RequiredAttribs.ACCOUNT: "--account",
        RequiredAttribs.QUEUE: "--qos",
        RequiredAttribs.WALLTIME: "--time",
    }


class PBS(JobScheduler):
    """
    Represents a PBS based scheduler.
    """

    prefix = "#PBS"
    key_value_separator = " "
    submit_command = "qsub"

    attrib_map = {
        OptionalAttribs.DEBUG: lambda x: f"-l debug={str(x).lower()}",
        OptionalAttribs.JOB_NAME: "-N",
        OptionalAttribs.MEMORY: "mem",
        OptionalAttribs.NODES: lambda x: f"-l select={x}",
        OptionalAttribs.SHELL: "-S",
        OptionalAttribs.STDOUT: "-o",
        OptionalAttribs.TASKS_PER_NODE: "mpiprocs",
        OptionalAttribs.THREADS: "ompthreads",
        RequiredAttribs.ACCOUNT: "-A",
        RequiredAttribs.QUEUE: "-q",
        RequiredAttribs.WALLTIME: "-l walltime=",
    }

    def pre_process(self) -> Dict[str, Any]:
        output = self.data
        output.update(self._select(output))
        output.update(self._placement(output))
        output.pop(OptionalAttribs.TASKS_PER_NODE, None)
        output.pop(OptionalAttribs.NODES, None)
        output.pop(OptionalAttribs.THREADS, None)
        output.pop(OptionalAttribs.MEMORY, None)
        output.pop("exclusive", None)
        output.pop("placement", None)
        output.pop("select", None)
        return dict(output)

    def _select(self, items: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select logic.
        """
        total_nodes = items.get(OptionalAttribs.NODES, "")
        tasks_per_node = items.get(OptionalAttribs.TASKS_PER_NODE, "")
        # Set default threads=1 to address job variability with PBS
        threads = items.get(OptionalAttribs.THREADS, 1)
        memory = items.get(OptionalAttribs.MEMORY, "")
        select = [
            f"{total_nodes}",
            f"{self.attrib_map[OptionalAttribs.TASKS_PER_NODE]}={tasks_per_node}",
            f"{self.attrib_map[OptionalAttribs.THREADS]}={threads}",
            f"ncpus={int(tasks_per_node) * int(threads)}",
        ]
        if memory:
            select.append(f"{self.attrib_map[OptionalAttribs.MEMORY]}={memory}")
        items["-l select="] = ":".join(select)
        return items

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


class LSF(JobScheduler):
    """
    Represents a LSF based scheduler.
    """

    prefix = "#BSUB"
    key_value_separator = " "
    submit_command = "bsub"

    attrib_map = {
        OptionalAttribs.JOB_NAME: "-J",
        OptionalAttribs.MEMORY: lambda x: f"-R rusage[mem={x}]",
        OptionalAttribs.NODES: lambda x: f"-n {x}",
        OptionalAttribs.SHELL: "-L",
        OptionalAttribs.STDOUT: "-o",
        OptionalAttribs.TASKS_PER_NODE: lambda x: f"-R span[ptile={x}]",
        OptionalAttribs.THREADS: lambda x: f"-R affinity[core({x})]",
        RequiredAttribs.ACCOUNT: "-P",
        RequiredAttribs.QUEUE: "-q",
        RequiredAttribs.WALLTIME: "-W",
    }

    def pre_process(self) -> Dict[str, Any]:
        items = self.data
        # LSF requires threads to be set (if None is provided, default to 1)
        items[OptionalAttribs.THREADS] = items.get(OptionalAttribs.THREADS, 1)
        nodes = items.get(OptionalAttribs.NODES, "")
        tasks_per_node = items.get(OptionalAttribs.TASKS_PER_NODE, "")
        memory = items.get(OptionalAttribs.MEMORY, None)
        if memory is not None:
            mem_value = Memory(memory).convert("KB")
            items[self.attrib_map[OptionalAttribs.MEMORY](mem_value)] = ""
        items[OptionalAttribs.NODES] = int(tasks_per_node) * int(nodes)
        items.pop(OptionalAttribs.MEMORY, None)
        return items
