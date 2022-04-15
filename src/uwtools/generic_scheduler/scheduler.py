from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

class Scheduler(ABC):
    def __init__(self, scheduler: str, job_name: str, partition: list, qos: str, output: Path, error: Path, walltime: datetime, account: str, nodes: int, ntasks_per_node: int, ntasks: int, cpus_per_task: int, reservation: str, join: bool, native_flags: list, run_command: str):
        self.scheduler = scheduler
        self.job_name = job_name
        self.partition = partition
        self.qos = qos
        self.output = output
        self.error = error
        self.walltime = walltime
        self.account = account
        self.nodes = nodes
        self.ntasks_per_node =ntasks_per_node
        self.ntasks = ntasks
        self.cpus_per_task = cpus_per_task
        self.reservation = reservation
        self.join = join
        self.native_flags = native_flags
        self.run_command = run_command

    @abstractmethod
    def add_native_flag(self, flag):
        pass

    def check_required_options(self):
        pass

    @abstractmethod
    def create_directive_list(self):
        pass

    @abstractmethod
    def join_output(self):
        pass

    def write_job_card(self):
        pass



