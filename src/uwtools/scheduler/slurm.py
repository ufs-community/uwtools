from io import StringIO
from .scheduler import Scheduler

__all__ = ['Slurm']


class Slurm(Scheduler):
    '''
    Class to construct Slurm job cards.
    For SBATCH reference see: https://slurm.schedmd.com/sbatch.html
    '''

    _DIRECTIVE = '#SBATCH'
    _MAPPING = {'account': '-A',
                'partition': '-p',
                ''}

    def __init__(self, config: dict, **kwargs):

        self._config = config

    def accounting(self, specs):
        '''
        Generate the accounting specific items of the job card.
        E.g. jobname, queuing, partitions, accounts etc.
        '''
        strings = []
        if 'jobname' in specs:
            strings.append(f"{self._DIRECTIVE} --job-name {specs.jobname}")
        if 'account' in specs:
            strings.append(f"{self._DIRECTIVE} --account {specs.account}")
        if 'queue' in specs:
            strings.append(f"{self._DIRECTIVE} --qos {specs.queue}")
        if 'partition' in specs and specs.partition:
            strings.append(f"{self._DIRECTIVE} --partition={specs.partition}")
        if 'join' in specs:
            strings.append(f"{self._DIRECTIVE} --error {specs.join}")
        else:
            if 'stdout' in specs:
                strings.append(f"{self._DIRECTIVE} --output {specs.stdout}")
            if 'stderr' in specs:
                strings.append(f"{self._DIRECTIVE} --error {specs.stderr}")

        return "\n".join(strings)


    def resources(self, specs):
        '''
        Generate the resource specific items of the job card.
        E.g. nodes, memory, walltime, exclusive, etc.
        '''
        strings = []

        return "\n".join(strings)

# Register Slurm as a builder in the scheduler_factory
Scheduler.scheduler_factory.register('Slurm', Slurm)
