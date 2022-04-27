"""
Job Scheduling
"""

import logging
import collections
from typing import Dict

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    handlers=[logging.StreamHandler()],
)


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

    @property
    def job_card(self):
        """returns the job card to be fed to external scheduler"""
        ignored_keys = ["scheduler"]

        known = [
            f"{self.prefix} {self._map[key]}{self.key_value_separator}{value}"
            for (key, value) in self.items()
            if key in self._map and key not in ignored_keys
        ]

        unknown = [
            f"{self.prefix} {key}{self.key_value_separator}{value}"
            for (key, value) in self.items()
            if key not in self._map
            and value not in [None, "", " ", "None", "none"]
            and key not in ignored_keys
        ]

        flags = [
            f"{self.prefix} {key}"
            for (key, value) in self.items()
            if key not in self._map
            and value in [None, "", " ", "None", "none"]
            and key not in ignored_keys
        ]

        return JobCard(sorted(known + unknown + flags))

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
            object: None,
        }  # TODO Does this need a default?
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


class PBS(JobScheduler):
    """represents a PBS based scheduler"""

    prefix = "#PBS"
    key_value_separator = " "

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
    key_value_separator = " "

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


if __name__ == "__main__":
    pass
