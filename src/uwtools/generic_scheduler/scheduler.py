"""
Scheduler base
"""

import abc
from datetime import datetime
from pathlib import Path


class Scheduler(abc.ABC):
    """represents an abstract scheduler"""

    def __init__(
        self,
        scheduler: str,
        job_name: str,
        partition: list,
        qos: str,
        output: Path,
        error: Path,
        walltime: datetime,
        account: str,
        nodes: int,
        ntasks_per_node: int,
        ntasks: int,
        cpus_per_task: int,
        reservation: str,
        join: bool,
        native_flags: list,
        run_command: str,
    ):
        pass

    @abc.abstractmethod
    def add_native_flag(self, flag):
        raise NotImplementedError

    def check_required_options(self):
        raise NotImplementedError

    @abc.abstractmethod
    def create_directive_list(self):
        raise NotImplementedError

    @abc.abstractmethod
    def join_output(self):
        raise NotImplementedError

    def write_job_card(self):
        raise NotImplementedError
