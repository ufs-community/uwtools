"""
Job Scheduling
"""

from abc import abstractmethod
import logging
import collections
import subprocess
from typing import Dict
import shelve

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    handlers=[logging.StreamHandler()],
)


def shelve_it(file_name):
    """persistent memoization"""
    d = shelve.open(file_name)

    def decorator(func):
        def new_func(param):
            if param not in d:
                d[param] = func(param)
            return d[param]

        return new_func

    return decorator


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

    def __getattr__(self, name):
        if name in self:
            return self[name]

    @property
    @abstractmethod
    def job_card(self) -> JobCard:
        raise NotImplementedError

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

        map_schedulers = {"slurm": Slurm, "pbs": PBS, "lsf": LSF, object: None}
        logging.debug("getting scheduler type %s", map_schedulers[props["scheduler"]])
        return map_schedulers[props["scheduler"]](props)


class Slurm(JobScheduler):
    """represents a Slurm based scheduler"""

    prefix = "#SBATCH"

    _map = {
        "job_name": "--job-name",
        "output": "--output",
        "error": "--error",
        "wall_time": "--time",
        "partition": "--partition",
        "account": "--account",
        "nodes": "--nodes",
        "number_tasks": "--ntasks-per-node",
    }

    @property
    def job_card(self) -> JobCard:
        """returns a JobCard object"""

        known = [
            f"{self.prefix} {self._map[key]}={value}"
            for (key, value) in self.items()
            if key in self._map
        ]

        unknown = [
            f"{self.prefix} {key}={value}"
            for (key, value) in self.items()
            if key not in self._map and value not in [None, "", " ", "None", "none"]
        ]

        flags = [
            f"{self.prefix} {key}"
            for (key, value) in self.items()
            if key not in self._map and value in [None, "", " ", "None", "none"]
        ]

        return JobCard(sorted(known + unknown + flags))


class PBS(JobScheduler):
    """represents a PBS based scheduler"""

    prefix = "#PBS"

    _map = {
        "shell": "-S",
        "job_name": "-N",
        "output": "-o",
        "job_name2": "-j",  # TODO 2 job name defs
        "queue": "-q",
        "account": "-A",
        "wall_time": "-l walltime=",
        "total_nodes": "-l select=",
        "cpus": "cpus=",
        "place": "-l place=",
        "debug": "-l debug=",
    }


class LSF(JobScheduler):
    """represents a LSF based scheduler"""

    prefix = "#BSUB"

    _map = {
        "shell": "-L",
        "job_name": "-J",
        "output": "-o",
        "queue": "-q",
        "account": "-P",
        "wall_time": "-W",
        "total_nodes": "-n",
        "cpus": "-R affinity[core()]",  # TODO
        "number_tasks": "-R span[ptile=]",  # TODO
        "change_dir": "-cwd /tmp",
    }


@shelve_it("cache.shelve")
def submit_job_card(content) -> int:
    """sends the job card to the scheduler for processing"""
    p = subprocess.Popen(
        ["sbatch", "--deadline=now+1"],
        stdin=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    stdout, stderr = p.communicate(input=content.encode())
    job_id = stdout.decode().split(" ")[-1]
    if stderr:
        raise BadJobCardError(stderr.decode().split("\n", maxsplit=1)[0])
    return int(job_id)


class Error(Exception):
    """base error"""


class BadJobCardError(Error):
    """unrecognized job card key/values"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


if __name__ == "__main__":
    pass
