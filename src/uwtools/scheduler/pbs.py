from .scheduler import Scheduler

__all__ = ['PBS']


class PBS(Scheduler):
    """
    Class to construct PBS job cards.
    There are several PBS implementations.
    This implementation supports the PBS Pro implementation from
    https://secure.altair.com/docs/PBSpro_UG_5_1.pdf
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
                'exclusive': '--exclusive',
                'debug': '--verbose',
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
        self.batch_card += strings

    @property
    def get_resources(self):
        """
        Generate the resource specific items of the job card.
        E.g. nodes, memory, walltime, exclusive, etc.
        """
        strings = []
        self.batch_card += strings

    @property
    def get_native(self):
        """
        Generate the scheduler specific native directives verbatim from the user input.
        """
        strings = []
        self.batch_card += strings

    @property
    def get_env(self):
        """
        Export environment variables
        """
        strings = []
        self.batch_card += strings


# Register PBS as a builder in the scheduler_factory
Scheduler.scheduler_factory.register('PBS', PBS)
