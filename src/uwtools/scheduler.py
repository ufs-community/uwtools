"""
Job Scheduling.
"""
from __future__ import annotations

import logging
import re
from collections import UserDict, UserList
from collections.abc import Mapping
from typing import Any, Dict, List

from uwtools.utils import Memory

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    handlers=[logging.StreamHandler()],
)

NONEISH = [None, "", " ", "None", "none", False]
IGNORED_ATTRIBS = ["scheduler"]


class RequiredAttribs:
    """
    Key for required attributes.
    """

    ACCOUNT = "account"
    QUEUE = "queue"
    WALLTIME = "walltime"
    NODES = "nodes"
    TASKS_PER_NODE = "tasks_per_node"


class OptionalAttribs:
    """
    Key for optional attributes.
    """

    SHELL = "shell"
    JOB_NAME = "jobname"
    STDOUT = "stdout"
    STDERR = "stderr"
    JOIN = "join"
    PARTITION = "partition"
    THREADS = "threads"
    MEMORY = "memory"
    DEBUG = "debug"
    EXCLUSIVE = "exclusive"
    PLACEMENT = "placement"


class JobCard(UserList):
    """
    Represents a job card to submit to a scheduler.
    """

    def __str__(self):
        """
        Returns string representation.
        """
        return str(self.content())

    def content(self, line_separator: str = "\n") -> str:
        """
        Returns the formatted content of the job cards.

        Parameters
        ----------
        line_separator
            The character or characters to join the content lines with
        """
        return line_separator.join(self)


class JobScheduler(UserDict):
    """
    Creates JobCard.
    """

    _map: dict = {}
    prefix = ""
    key_value_separator = "="

    def __init__(self, props):
        super().__init__(props)
        self.validate_props(props)

    def __getattr__(self, name) -> Any:
        if name in self:
            return self[name]
        raise AttributeError(name)

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

    def pre_process(self) -> Dict[str, Any]:
        """
        Pre-process attributes before converting to job card.
        """
        return self.data

    @staticmethod
    def post_process(items: List[str]) -> List[str]:
        """
        Post process attributes before converting to job card.
        """
        return [re.sub(r"\s{0,}\=\s{0,}", "=", x, count=0, flags=0) for x in items]

    @property
    def job_card(self) -> JobCard:
        """
        Returns the job card to be fed to external scheduler.
        """

        sanitized_attribs = self.pre_process()

        known = []
        for key, value in sanitized_attribs.items():
            if key in self._map and key not in IGNORED_ATTRIBS:
                scheduler_flag = (
                    self._map[key](value) if callable(self._map[key]) else self._map[key]
                )
                scheduler_value = "" if callable(self._map[key]) else value
                directive = (
                    f"{self.prefix} {scheduler_flag}{self.key_value_separator}{scheduler_value}"
                )
                known.append(directive.strip())

        unknown = [
            f"{self.prefix} {key}{self.key_value_separator}{value}".strip()
            for (key, value) in sanitized_attribs.items()
            if key not in self._map and value not in NONEISH and key not in IGNORED_ATTRIBS
        ]

        flags = [
            f"{self.prefix} {key}".strip()
            for (key, value) in sanitized_attribs.items()
            if value in NONEISH
        ]

        processed = self.post_process(known + unknown + flags)

        # Sort batch directives to normalize output w.r.t. potential differences
        # in ordering of input dicts.

        return JobCard(sorted(processed))

    @staticmethod
    def get_scheduler(props: Mapping) -> JobScheduler:
        """
        Returns the appropriate scheduler.

        Parameters
        ----------
        props
            Must contain a 'scheduler' key or a KeyError will be raised
        """
        if "scheduler" not in props:
            raise KeyError(f"No scheduler defined in props: [{', '.join(props.keys())}]")
        name = props["scheduler"]
        logging.debug("Getting '%s' scheduler", name)
        schedulers = {"slurm": Slurm, "pbs": PBS, "lsf": LSF}
        try:
            scheduler = schedulers[name]
        except KeyError as error:
            raise KeyError(
                f"{name} is not a supported scheduler"
                + "Currently supported schedulers are:\n"
                + f'{" | ".join(schedulers.keys())}"'
            ) from error
        return scheduler(props)


class Slurm(JobScheduler):
    """
    Represents a Slurm based scheduler.
    """

    prefix = "#SBATCH"

    _map = {
        RequiredAttribs.ACCOUNT: "--account",
        RequiredAttribs.NODES: "--nodes",
        RequiredAttribs.QUEUE: "--qos",
        RequiredAttribs.TASKS_PER_NODE: "--ntasks-per-node",
        RequiredAttribs.WALLTIME: "--time",
        OptionalAttribs.JOB_NAME: "--job-name",
        OptionalAttribs.STDOUT: "--output",
        OptionalAttribs.STDERR: "--error",
        OptionalAttribs.PARTITION: "--partition",
        OptionalAttribs.THREADS: "--cpus-per-task",
        OptionalAttribs.MEMORY: "--mem",
        OptionalAttribs.EXCLUSIVE: "--exclusive",
    }


class PBS(JobScheduler):
    """
    Represents a PBS based scheduler.
    """

    prefix = "#PBS"
    key_value_separator = " "

    _map = {
        RequiredAttribs.ACCOUNT: "-A",
        RequiredAttribs.NODES: lambda x: f"-l select={x}",
        RequiredAttribs.QUEUE: "-q",
        RequiredAttribs.WALLTIME: "-l walltime=",
        RequiredAttribs.TASKS_PER_NODE: "mpiprocs",
        OptionalAttribs.SHELL: "-S",
        OptionalAttribs.JOB_NAME: "-N",
        OptionalAttribs.STDOUT: "-o",
        OptionalAttribs.DEBUG: lambda x: f"-l debug={str(x).lower()}",
        OptionalAttribs.THREADS: "ompthreads",
        OptionalAttribs.MEMORY: "mem",
    }

    def pre_process(self) -> Dict[str, Any]:
        output = self.data
        output.update(self._select(output))
        output.update(self._placement(output))

        output.pop(RequiredAttribs.TASKS_PER_NODE, None)
        output.pop(RequiredAttribs.NODES, None)
        output.pop(OptionalAttribs.THREADS, None)
        output.pop(OptionalAttribs.MEMORY, None)
        output.pop("exclusive", None)
        output.pop("placement", None)
        output.pop("select", None)
        return dict(output)

    def _select(self, items) -> Dict[str, Any]:
        """
        Select logic.
        """
        total_nodes = items.get(RequiredAttribs.NODES, "")
        tasks_per_node = items.get(RequiredAttribs.TASKS_PER_NODE, "")
        # Set default threads=1 to address job variability with PBS
        threads = items.get(OptionalAttribs.THREADS, 1)
        memory = items.get(OptionalAttribs.MEMORY, "")

        select = [
            f"{total_nodes}",
            f"{self._map[RequiredAttribs.TASKS_PER_NODE]}={tasks_per_node}",
            f"{self._map[OptionalAttribs.THREADS]}={threads}",
            f"ncpus={int(tasks_per_node) * int(threads)}",
        ]
        if memory not in NONEISH:
            select.append(f"{self._map[OptionalAttribs.MEMORY]}={memory}")
        items["-l select="] = ":".join(select)

        return items

    @staticmethod
    def _placement(items) -> Dict[str, Any]:
        """
        Placement logic.
        """

        exclusive = items.get(OptionalAttribs.EXCLUSIVE, "")
        placement = items.get(OptionalAttribs.PLACEMENT, "")

        if all(
            [
                exclusive in NONEISH,
                placement in NONEISH,
            ]
        ):
            return items

        output = []
        if placement not in NONEISH:
            output.append(str(placement))
        if exclusive not in NONEISH:
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

    _map = {
        RequiredAttribs.QUEUE: "-q",
        RequiredAttribs.ACCOUNT: "-P",
        RequiredAttribs.WALLTIME: "-W",
        RequiredAttribs.NODES: lambda x: f"-n {x}",
        RequiredAttribs.TASKS_PER_NODE: lambda x: f"-R span[ptile={x}]",
        OptionalAttribs.SHELL: "-L",
        OptionalAttribs.JOB_NAME: "-J",
        OptionalAttribs.STDOUT: "-o",
        OptionalAttribs.THREADS: lambda x: f"-R affinity[core({x})]",
        OptionalAttribs.MEMORY: lambda x: f"-R rusage[mem={x}]",
    }

    def pre_process(self) -> Dict[str, Any]:
        items = self.data
        # LSF requires threads to be set (if None is provided, default to 1)
        items[OptionalAttribs.THREADS] = items.get(OptionalAttribs.THREADS, 1)
        nodes = items.get(RequiredAttribs.NODES, "")
        tasks_per_node = items.get(RequiredAttribs.TASKS_PER_NODE, "")

        memory = items.get(OptionalAttribs.MEMORY, None)
        if memory is not None:
            mem_value = Memory(memory).convert("KB")
            items[self._map[OptionalAttribs.MEMORY](mem_value)] = ""

        items[RequiredAttribs.NODES] = int(tasks_per_node) * int(nodes)
        items.pop(OptionalAttribs.MEMORY, None)
        return items
