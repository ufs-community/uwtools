from .scheduler import Scheduler
from datetime import datetime
from pathlib import Path

__all__ = ['Slurm']

class Slurm(Scheduler):
    _DIRECTIVE = '#SBATCH'

    def __init__(self, scheduler: str, job_name: str, partition: list, qos: str, output: Path, error: Path, walltime: datetime, account: str, nodes: int, ntasks_per_node: int, ntasks: int, cpus_per_task: int, reservation: str, join: bool, native_flags: list, run_command: str):
        super().__init__(scheduler, job_name, partition, qos, output, error, walltime, account, nodes, ntasks_per_node, ntasks, cpus_per_task, reservation, join, native_flags, run_command)
        
    def map_flags():
        mappings = {'account': '-A', 'partition': '-p', 'wallclock': '-t', 'job_name': '-J', 'nodes': '-N', 'ntasks_per_node': '-n', 'output': '-o', 'error': '-e'}
        return mappings

    def add_native_flag(flag):
        pass

    def create_directive_list(self,specs):
        '''
        Generate the account specific items of the job card.
        '''
        strings = []
        if 'jobname' in specs:
            strings.append(f"{self._DIRECTIVE} --job-name {specs.jobname}")
        if 'account' in specs:
            strings.append(f"{self._DIRECTIVE} --account {specs.account}")
        if 'walltime' in specs:
            strings.append(f"{self._DIRECTIVE} --time {specs.walltime}")
        if 'partition' in specs and specs.partition:
            strings.append(f"{self._DIRECTIVE} --partition={specs.partition}")
        if 'nodes' in specs:
            strings.append(f"{self._DIRECTIVE} --nodes={specs.nodes}")
        if 'ntasks_per_node' in specs:
            strings.append(f"{self._DIRECTIVE} --ntasks_per_node={specs.ntasks_per_node}")
        if 'join' in specs:
            strings.append(f"{self._DIRECTIVE} --error {specs.join}")
        else:
            if 'stdout' in specs:
                strings.append(f"{self._DIRECTIVE} --output {specs.stdout}")
            if 'stderr' in specs:
                strings.append(f"{self._DIRECTIVE} --error {specs.stderr}")
        return "\n".join(strings)