"""
Job Scheduling
"""

import logging
import collections
from typing import Any, Callable, Dict, List


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    handlers=[logging.StreamHandler()],
)


class RequiredAttribs:  # pylint: disable=too-few-public-methods
    """key for required attributes"""

    ACCOUNT = "account"
    QUEUE = "queue"
    WALLTIME = "wall_time"
    NODES = "nodes"
    TASKS_PER_NODE = "tasks_per_node"


class OptionalAttribs:  # pylint: disable=too-few-public-methods
    """key for optional attributes"""

    SHELL = "shell"
    JOB_NAME = "job_name"
    STDOUT = "stdout"
    STDERR = "stderr"
    JOIN = "join"
    PARTITION = "partition"
    THREADS = "threads"
    MEMORY = "memory"
    DEBUG = "debug"
    EXCLUSIVE = "exclusive"
    NATIVE = "native"
    CPUS = "cpus"


class AttributeMap(collections.UserDict):
    def __init__(self, _map):
        super().__init__()
        self.update(self._parsed(_map))

    def _parsed(self, raw_map):

        return {
            raw_map[key](value)
            if callable(raw_map[key])
            else key: value
            if not callable(value)
            else ""
            for (key, value) in raw_map.items()
        }


class JobCard(collections.UserList):
    """represents a job card to submit to a scheduler"""

    def content(self, line_separator: str = "\n") -> str:
        """returns the formatted content of the job cards

        Parameters
        ----------
        line_separator : str
            the character or characters to join the content lines on.
        """
        return line_separator.join(self)


class JobScheduler(collections.UserDict):
    """object that creates JobCard"""

    _map = {}
    prefix = ""
    key_value_separator = "="

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(name)

    def pre_process(self):
        """pre process attributes before converting to job card"""
        return self

    @staticmethod
    def post_process(items: List[Any]):
        """post process attributes before converting to job card"""
        return items

    @property
    def job_card(self):
        """returns the job card to be fed to external scheduler"""
        ignored_keys = ["scheduler"]
        sanitized_attribs = AttributeMap(self.pre_process())
        print(sanitized_attribs)

        known = [
            f"{self.prefix} {self._map[key]}{self.key_value_separator}{value}"
            for (key, value) in sanitized_attribs.items()
            if key in self._map and key not in ignored_keys
        ]

        unknown = [
            f"{self.prefix} {key}{self.key_value_separator}{value}"
            for (key, value) in sanitized_attribs.items()
            if key not in self._map
            and value not in [None, "", " ", "None", "none"]
            and key not in ignored_keys
        ]

        flags = [
            f"{self.prefix} {key}"
            for (key, value) in sanitized_attribs.items()
            if key not in self._map
            and value in [None, "", " ", "None", "none"]
            and key not in ignored_keys
        ]

        processed = sorted(known + unknown + flags)

        return JobCard(processed)

    @classmethod
    def get_scheduler(cls, props: Dict[str, str]) -> "JobScheduler":
        """returns the appropriate scheduler

        Parameters
        ----------
        props : dict
            must contain a scheduler key or raise KeyError

        TODO: map_schedulers should be hoisted up out of the method
        """
        if "scheduler" not in props:
            raise KeyError(
                f"no scheduler defined in props: [{', '.join(props.keys())}]"
            )

        map_schedulers = {
            "slurm": Slurm,
            "pbs": PBS,
            "lsf": LSF,
        }
        logging.debug("getting scheduler type %s", map_schedulers[props["scheduler"]])
        try:
             return map_schedulers[props["scheduler"]](props)
        except KeyError:
             raise KeyError(f"{props['scheduler']} is not a supported scheduler" +
                           "Currently supported schedulers are:\n" + 
                           f'{" | ".join(map_schedulers.keys())}"')


class Slurm(JobScheduler):
    """represents a Slurm based scheduler"""

    prefix = "#SBATCH"

    _map = AttributeMap(
        {
            RequiredAttribs.ACCOUNT: "--account",
            RequiredAttribs.NODES: "--nodes",
            RequiredAttribs.QUEUE: "--qos",  # TODO verify, placeholder
            RequiredAttribs.TASKS_PER_NODE: "--ntasks-per-node",
            RequiredAttribs.WALLTIME: "--time",
            OptionalAttribs.JOB_NAME: "--job-name",
            OptionalAttribs.STDOUT: "--output",
            OptionalAttribs.STDERR: "--error",
            OptionalAttribs.PARTITION: "--partition",
        }
    )


class PBS(JobScheduler):
    """represents a PBS based scheduler"""

    prefix = "#PBS"
    key_value_separator = " "

    _map = AttributeMap(
        {
            RequiredAttribs.ACCOUNT: "-A",
            RequiredAttribs.NODES: (lambda x: f"-l select={x}"),
            RequiredAttribs.QUEUE: "-q",
            RequiredAttribs.TASKS_PER_NODE: "ncpus=",
            RequiredAttribs.WALLTIME: "-l walltime=",
            OptionalAttribs.SHELL: "-S",
            OptionalAttribs.JOB_NAME: "-N",
            OptionalAttribs.STDOUT: "-o",
            OptionalAttribs.DEBUG: "-l debug=",
            OptionalAttribs.CPUS: ":mpiprocs=",
            OptionalAttribs.THREADS: ":ompthreads=",
        }
    )

    def post_process(self, items):
        print(items)
        select = f"{items.pop(RequiredAttribs.NODES)}{items.pop(OptionalAttribs.CPUS)}{items.pop(OptionalAttribs.THREADS)}{items.pop(RequiredAttribs.TASKS_PER_NODE)}"
        items.append(select)
        return items


class LSF(JobScheduler):
    """represents a LSF based scheduler"""

    prefix = "#BSUB"
    key_value_separator = " "

    _map = AttributeMap(
        {
            RequiredAttribs.QUEUE: "-q",
            RequiredAttribs.ACCOUNT: "-P",
            RequiredAttribs.WALLTIME: "-W",
            RequiredAttribs.NODES: "-n",
            RequiredAttribs.TASKS_PER_NODE: lambda x: f"-R span[ptile={x}]",
            OptionalAttribs.SHELL: "-L",
            OptionalAttribs.JOB_NAME: "-J",
            OptionalAttribs.STDOUT: "-o",
            OptionalAttribs.CPUS: lambda x: f"-R affinity[core({x})]",
        }
    )


if __name__ == "__main__":
    pass
