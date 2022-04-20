from src.uwtools.scheduler.scheduler import Scheduler
from enum import Enum, auto


# Using enum.auto() method
class CommandKey(Enum):
    JOB_NAME = auto()
    OUTPUT = auto()
    ERROR = auto()
    TIME = auto()
    PARTITION = auto()
    ACCOUNT = auto()
    NODES = auto()
    NTASKS = auto()
    WALL_TIME = auto()
    QUEUE = auto()
    TOTAL_NODES = auto()
    CPUS = auto()
    PLACE = auto()
    DEBUG = auto()
    BASH = auto()
    CHANGE_DIR = auto()


class Slurm(Scheduler):
    _map = {
        CommandKey.JOB_NAME: "--job-name=",
        CommandKey.OUTPUT: "--output=",
        CommandKey.ERROR: "--error=",
        CommandKey.WALL_TIME: "--time=",
        CommandKey.PARTITION: "--partition=",
        CommandKey.ACCOUNT: "--account=",
        CommandKey.NODES: "--nodes=",
        CommandKey.NTASKS: "--ntasks-per-node=",
    }

    prefix = "#SBATCH"

    pass


class Bash(Scheduler):
    prefix = ""
    pass


class PBS(Scheduler):
    _map = {
        CommandKey.BASH: "-S",
        CommandKey.JOB_NAME: "-N",
        CommandKey.OUTPUT: "-o",
        CommandKey.JOB_NAME: "-j",
        CommandKey.QUEUE: "-q",
        CommandKey.ACCOUNT: "-A",
        CommandKey.WALL_TIME: "-l walltime=",
        CommandKey.TOTAL_NODES: "-l select=",
        CommandKey.CPUS: "cpus=",
        CommandKey.PLACE: "-l place=",
        CommandKey.DEBUG: "-l debug=",
    }

    prefix = "#PBS"
    pass


class LSF(Scheduler):
    _map = {
        CommandKey.BASH: "-L",
        CommandKey.JOB_NAME: "-J",
        CommandKey.OUTPUT: "-o",
        CommandKey.QUEUE: "-q",
        CommandKey.ACCOUNT: "-P",
        CommandKey.WALL_TIME: "-W",
        CommandKey.TOTAL_NODES: "-n",
        CommandKey.CPUS: "-R affinity[core()]", # TODO 
        CommandKey.NTASKS: "-R span[ptile=]", # TODO
        CommandKey.CHANGE_DIR: "-cwd /tmp",
    }

    prefix = "#BSUB"
    pass
