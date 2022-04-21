import os
from .scheduler import Scheduler

__all__ = ['PBS']


class PBS(Scheduler):
    """
    Class to construct PBS job cards.
    There are several PBS implementations.
    This implementation supports the PBS Pro implementation from
    https://www.altair.com/pdfs/pbsworks/PBSUserGuide2021.1.pdf
    """

    _DIRECTIVE = '#PBS'
    _MAPPING = {'account': '-A',
                'queue': '-q',
                'jobname': '-N',
                'stdout': '-o',
                'stderr': '-e',
                'join': '-j',
                'walltime': '-l walltime',
                'env': '-V',
                'nodes': '--nodes',
                'tasks': '--ntasks',
                'tasks_per_core': '--ntasks_per-core',
                'tasks_per_node': '--ntasks_per-node',
                'memory': '--mem',
                'shell': '-S',
                'debug': '-l debug',
                'mail': '-M'}

    def __init__(self, config: dict, *args, **kwargs):
        """

        Parameters
        ----------
        config
        args
        kwargs

        Returns
        -------
        object
        """
        super().__init__(config, *args, **kwargs)

        self.batch_card += self.get_accounting
        self.batch_card += self.get_resources
        self.batch_card += self.get_native
        self.batch_card += self.get_env

    @property
    def get_accounting(self):
        """
        Generate the accounting specific items of the job card.
        E.g. jobname, queuing, partitions, accounts etc.
        """
        strings = []

        if 'shell' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['shell']} {self.specs.shell}")
        if 'jobname' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['jobname']} {self.specs.jobname}")
        if 'account' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['account']} {self.specs.account}")
        if 'queue' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['queue']} {self.specs.queue}")
        if 'join' in self.specs and self.specs.join:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['join']} oe")
        if 'stdout' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['stdout']} {self.specs.stdout}")
        elif 'stderr' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['stderr']} {self.specs.stderr}")

        return strings

    @property
    def get_resources(self):
        """
        Generate the resource specific items of the job card.
        E.g. nodes, memory, walltime, exclusive, etc.
        """
        strings = []
        if 'walltime' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['walltime']}={self.specs.walltime}")
        if 'debug' in self.specs:
            strings.append(f"{self._DIRECTIVE} {self._MAPPING['debug']}={self.specs.debug}")
        select = self.get_select
        if select:
            strings.append(f"{self._DIRECTIVE} -l select={select}")
        place = self.get_place
        if place:
            strings.append(f"{self._DIRECTIVE} -l place={place}")

        return strings

    @property
    def get_env(self):
        """
        Export environment variables
        """
        strings = []
        if 'env' in self.specs:
            if any(item.upper() in 'ALL' for item in self.specs.env):
                strings.append(f"{self._DIRECTIVE} -V")
            else:
                env_list = []
                for item in self.specs.env:
                    env_list.append(f"{item}={os.getenv(item)}")
                strings.append(f"#PBS -v {','.join(env_list)}")

        return strings

    @property
    def get_select(self):
        """
        Construct the "select" resource request for the job
        Returns
        -------
        #PBS -l select=<get_select>

        """
        strings = []
        if 'nodes' in self.specs:
            strings.append(f"{self.specs.nodes}")
        if 'tasks_per_node' in self.specs:
            strings.append(f"mpiprocs={self.specs.tasks_per_node}")
        if 'threads' in self.specs:
            strings.append(f"ompthreads={self.specs.threads}")
        if 'tasks' in self.specs:
            strings.append(f"ncpus={self.specs.tasks}")
        if 'memory' in self.specs:
            strings.append(f"mem={self.specs.memory}")

        return ':'.join(strings)

    @property
    def get_place(self):
        """
        Construct the "place" placement request for the job
        Returns
        -------
        #PBS -l place=<get_place>

        """
        strings = []
        if 'chunk' in self.specs:
            # Valid options are: free, pack, scatter, vscatter
            strings.append(f"{self.specs.chunk}")
        if 'exclusive' in self.specs and self.specs.exclusive:
            strings.append('excl')

        return ':'.join(strings)


# Register PBS as a builder in the scheduler_factory
Scheduler.scheduler_factory.register('PBS', PBS)
