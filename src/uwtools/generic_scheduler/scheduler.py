import abc
from ast import List
from datetime import datetime
from importlib.resources import path
from msilib.schema import ListView
from pathlib import Path


class Scheduler:
    def __init__(self, scheduler: str, job_name: str, partition: list, qos: str, output: Path, error: Path, walltime: datetime, account: str, nodes: int, ntasks_per_node: int, ntasks: int, cpus_per_task: int, reservation: str, join: bool, native_flags: list, run_command: str):
        pass
    @abc.abstractmethod
    def add_native_flag(flag):
        pass
    def check_required_options():
        pass
    @abc.abstractmethod
    def create_directive_list():
        pass
    @abc.abstractmethod
    def join_output():
        pass

    def write_job_card():
        pass



