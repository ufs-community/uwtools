from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

class Scheduler(ABC):
    def __init__(self, scheduler: str, job_name: str, partition: list,
            qos: str, output: Path, error: Path, walltime: datetime,
            account: str, nodes: int, ntasks_per_node: int, ntasks: int,
            cpus_per_task: int, reservation: str, join: bool,
            native_flags: list, run_command: str, job_card_path: Path):
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
        self.job_card_path = job_card_path

    def add_native_flag(self, flag):
        self.flag = flag
        self.directives.append(self.native_flags)

    def check_required_options(self):
        ''' Not sure what this thing does at this point. '''
        pass

    def _create_directive_list(self: list):

        ''' Uses the map_flags dict from subclass to build a directives list.
        '''
        # Add in dict logic from PR comment here.
        

    @abstractmethod
    def join_output(self):

        ''' Different schedulers handle the joining of output by removal
        of flags and/or the addition of other flags. PBS, for example,
        requires the addition of "-j oe" to join output, and Slurm
        requires that only the -o flag is provided. '''

        pass

    @property
    def directives(self):
        ret = self._create_directive_list()
        if self.native_flags:
            self.add_native_flag()

        if self.join:
            self.join_output()
        return ret

    def write_job_card(self):

        with open(self.job_card_path) as fn:
            fn.write('\n'.join(self.directives))
            fn.write(self.run_command)

