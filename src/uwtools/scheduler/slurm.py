# from io import StringIO
from .scheduler import Scheduler

__all__ = ['Slurm']


class Slurm(Scheduler):
    """
    Class to construct Slurm job cards.
    For SBATCH reference see: https://slurm.schedmd.com/sbatch.html
    """

    _DIRECTIVE = '#SBATCH'
    _MAPPING = {'account': '--account',
                'partition': '--partition',
                'queue': '--qos',
                'jobname': '--job-name',
                'stdout': '--output',
                'stderr': '--error',
                'walltime': '--time',
                'env': '--export',
                'nodes': '--nodes',
                'tasks': '--ntasks',
                'tasks_per_core': '--ntasks_per-core',
                'tasks_per_node': '--ntasks_per-node',
                'memory': '--mem',
                'exclusive': '--exclusive',
                'debug': '--verbose'}

    def __init__(self, config: dict, *args, **kwargs):
        """
        Constructor for Slurm scheduler.

        Parameters
        ----------
        config : dict
        """

        super().__init__(config, *args, **kwargs)

        self.get_accounting
        self.get_resources
        self.get_native
        self.get_env

    @property
    def get_accounting(self):
        """
        Generate the accounting specific items of the job card.
        E.g. jobname, queuing, partitions, accounts etc.
        """
        strings = []
        if 'jobname' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['jobname']}={self.specs.jobname}")
        if 'account' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['account']}={self.specs.account}")
        if 'queue' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['queue']}={self.specs.queue}")
        if 'partition' in self.specs and self.specs.partition:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['partition']}={self.specs.partition}")
        if 'join' in self.specs and self.specs.join:
            if 'stdout' in self.specs:
                joined_output = self.specs.stdout
            else:
                joined_output = self.specs.stderr if 'stderr' in self.specs else None
            if joined_output is not None:
                strings.append(f"{self._DIRECTIVE} {self._MAPPING['stderr']}={joined_output}")
        else:
            if 'stdout' in self.specs:
                strings.append(f"{self._DIRECTIVE} {self._MAPPING['stdout']}={self.specs.stdout}")
            if 'stderr' in self.specs:
                strings.append(f"{self._DIRECTIVE} {self._MAPPING['stderr']}={self.specs.stderr}")

        self.batch_card += strings

    @property
    def get_resources(self):
        """
        Generate the resource specific items of the job card.
        E.g. nodes, memory, walltime, exclusive, etc.
        """
        strings = []
        if 'memory' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['memory']}={self.specs.memory}")
        if 'walltime' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['walltime']}={self.specs.walltime}")
        if 'nodes' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['nodes']}={self.specs.nodes}")
        if 'tasks_per_core' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['tasks_per_core']}={self.specs.tasks_per_core}")
        if 'tasks_per_node' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['tasks_per_node']}={self.specs.tasks_per_node}")
        if 'exclusive' in self.specs and self.specs.exclusive:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['exclusive']}")
        if 'debug' in self.specs and self.specs.debug:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['debug']}")

        self.batch_card += strings

    @property
    def get_native(self):
        """
        Generate the scheduler specific native directives verbatim from the user input.
        """
        strings = []
        if 'native' in self.specs:
            for item in self.specs.native:
                strings.append(f"{self._DIRECTIVE} {item}")

        self.batch_card += strings

    @property
    def get_env(self):
        """
        Export environment variables
        """
        strings = []
        if 'env' in self.specs:
            for item in self.specs.env:
                strings.append(f"{self._DIRECTIVE} {self._MAPPING['env']}={item}")

        self.batch_card += strings


# Register Slurm as a builder in the scheduler_factory
Scheduler.scheduler_factory.register('Slurm', Slurm)

