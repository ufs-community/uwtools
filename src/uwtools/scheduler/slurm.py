from typing import Any, Dict
from src.uwtools.scheduler.scheduler import Scheduler
from enum import Enum, auto

from string import Template


class Slurm(Scheduler):
    prefix = "#SBATCH"

    _map = {
        "job_name": "--job-name=",
        "output": "--output=",
        "error": "--error=",
        "wall_time": "--time=",
        "partition": "--partition=",
        "account": "--account=",
        "nodes": "--nodes=",
        "number_tasks": "--ntasks-per-node=",
    }


class Bash(Scheduler):
    prefix = ""


class PBS(Scheduler):
    prefix = "#PBS"

    _map = {
        "bash": "-S",
        "job_name": "-N",
        "output": "-o",
        "job_name": "-j",
        "queue": "-q",
        "account": "-A",
        "wall_time": "-l walltime=",
        "total_nodes": "-l select=",
        "cpus": "cpus=",
        "place": "-l place=",
        "debug": "-l debug=",
    }


class LSF(Scheduler):
    _map = {
        "bash": "-L",
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

    prefix = "#BSUB"
    pass
