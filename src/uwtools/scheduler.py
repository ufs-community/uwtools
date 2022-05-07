"""
Job Scheduling
"""
import collections
import logging

from typing import Any, Dict, List

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    handlers=[logging.StreamHandler()],
)

NONEISH = [None, "", " ", "None", "none", False]
IGNORED_ATTRIBS = ["scheduler"]


class RequiredAttribs:  # pylint: disable=too-few-public-methods
    """key for required attributes"""

    ACCOUNT = "account"
    QUEUE = "queue"
    WALLTIME = "walltime"
    NODES = "nodes"
    TASKS_PER_NODE = "tasks_per_node"


class OptionalAttribs:  # pylint: disable=too-few-public-methods
    """key for optional attributes"""

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

    def __init__(self, props):
        super().__init__()
        self.validate_props(props)
        self.update(props)

    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(name)

    def validate_props(self, props):
        members = [
            getattr(RequiredAttribs, attr)
            for attr in dir(RequiredAttribs)
            if not callable(getattr(RequiredAttribs, attr))
            and not attr.startswith("__")
        ]

        diff = [x for x in members if x not in props]
        if len(diff):
            raise ValueError(f"missing required attributes: [{', '.join(diff)}]")

    @property
    def _data(self):
        return self.__dict__["data"]

    def pre_process(self):
        """pre process attributes before converting to job card"""
        return self._data

    @staticmethod
    def post_process(items: List[str]):
        """post process attributes before converting to job card"""
        # TODO use regex
        output = items
        output = [x.replace("= ", "=") for x in output]
        output = [x.replace(" =", "=") for x in output]
        output = [x.replace(" = ", "=") for x in output]
        return output

    @property
    def job_card(self):
        """returns the job card to be fed to external scheduler"""
        sanitized_attribs = self.pre_process()

        known = [
            f"{self.prefix} {self._map[key](value) if callable(self._map[key]) else self._map[key]}{self.key_value_separator}{value if not callable(self._map[key]) else ''}".strip()
            for (key, value) in sanitized_attribs.items()
            if key in self._map and key not in IGNORED_ATTRIBS
        ]  # TODO seems bloated

        unknown = [
            f"{self.prefix} {key}{self.key_value_separator}{value}".strip()
            for (key, value) in sanitized_attribs.items()
            if key not in self._map
            and value not in NONEISH
            and key not in IGNORED_ATTRIBS
        ]

        flags = [
            f"{self.prefix} {value}".strip()
            for (key, value) in sanitized_attribs.items()
            if key in NONEISH
        ]

        processed = self.post_process(known + unknown + flags)

        return JobCard(processed)

    @classmethod
    def get_scheduler(cls, props: Dict[str, Any]) -> "JobScheduler":
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
        except KeyError as error:
            raise KeyError(
                f"{props['scheduler']} is not a supported scheduler"
                + "Currently supported schedulers are:\n"
                + f'{" | ".join(map_schedulers.keys())}"'
            ) from error


class Slurm(JobScheduler):
    """represents a Slurm based scheduler"""

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
    """represents a PBS based scheduler"""

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
        output = self._data
        output.update(self.select(output))
        output.update(self.placement(output))

        output.pop(RequiredAttribs.TASKS_PER_NODE, None)
        output.pop(RequiredAttribs.NODES, None)
        output.pop(OptionalAttribs.THREADS, None)
        output.pop(OptionalAttribs.MEMORY, None)
        output.pop("exclusive", None)
        output.pop("placement", None)
        output.pop("select", None)
        return dict(output)

    def select(self, items) -> Dict[str, Any]:
        """select logic"""
        total_nodes = items.get(RequiredAttribs.NODES, "")
        tasks_per_node = items.get(RequiredAttribs.TASKS_PER_NODE, "")
        threads_per_core = items.get(OptionalAttribs.THREADS, "")
        memory = items.get(OptionalAttribs.MEMORY, "")

        items["-l select"] = f"={total_nodes}:{self._map[RequiredAttribs.TASKS_PER_NODE]}={tasks_per_node}"
        if threads_per_core not in NONEISH:
            items[
                "-l select"
            ] = f"{items['-l select']}:{self._map[OptionalAttribs.THREADS]}={threads_per_core}:ncpus={int(tasks_per_node) * int(threads_per_core)}"
        if memory not in NONEISH:
            items["-l select"] = f"{items['-l select']}:{self._map[OptionalAttribs.MEMORY]}={memory}"
        return items

    def placement(self, items) -> Dict[str, Any]:
        """placement logic"""

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
    """represents a LSF based scheduler"""

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

    def pre_process(self):
        items = self._data
        items[self._map[OptionalAttribs.THREADS](items[OptionalAttribs.THREADS])] = ""
        memory = items.get(OptionalAttribs.MEMORY, "")
        if memory not in NONEISH:
            items[self._map[OptionalAttribs.MEMORY](items[OptionalAttribs.MEMORY])] = ""
        items[
            self._map[RequiredAttribs.TASKS_PER_NODE](
                items[RequiredAttribs.TASKS_PER_NODE]
            )
        ] = ""
        items[RequiredAttribs.NODES] = int(items[RequiredAttribs.TASKS_PER_NODE] * int(items[RequiredAttribs.NODES]))
        return items


if __name__ == "__main__":
    pass
