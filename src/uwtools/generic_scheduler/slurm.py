from .scheduler import Scheduler
from datetime import datetime
from pathlib import Path

__all__ = ['Slurm']

class Slurm(Scheduler):
    _DIRECTIVE = '#SBATCH'

    def __init__(self, scheduler: str, job_name: str, partition: list, qos: str, output: Path, error: Path, walltime: datetime, account: str, nodes: int, ntasks_per_node: int, ntasks: int, cpus_per_task: int, reservation: str, join: bool, native_flags: list, run_command: str, mappings: object):
        super().__init__(scheduler, job_name, partition, qos, output, error, walltime, account, nodes, ntasks_per_node, ntasks, cpus_per_task, reservation, join, native_flags, run_command)
        
    
    mappings = {'-A': 'account', '-p': 'partition', '-t': 'wallclock', '-J':'job_name', '-N': 'nodes', '-n': 'tasks_per_node', '-o': 'output', '-e': 'error'}

    def add_native_flag(flag):

        strings = []
        if 'native' in self.specs:
            for item in self.specs.native:
                strings.append(f"{self._DIRECTIVE} {item}")

        return strings

    def create_directive_list(self,specs):
        '''
        Generate the account specific items of the job card.
        '''
        strings = []
        for flag, setting in self.map_flags.items():
            strings.append(f"{self._DIRECTIVE} --{flag}={setting}")
        if 'join' in specs:
            strings.append(f"{self._DIRECTIVE} --error {specs.join}")
        else:
            if 'stdout' in specs:
                strings.append(f"{self._DIRECTIVE} --output {specs.stdout}")
            if 'stderr' in specs:
                strings.append(f"{self._DIRECTIVE} --error {specs.stderr}")
        return "\n".join(strings)

    def join_output(self):
        if self.join:
            if '-e' in self.map_flags:
                self.map_flags.pop('-e')
