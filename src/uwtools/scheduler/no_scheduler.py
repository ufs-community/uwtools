from .scheduler import Scheduler

__all__ = ['NoScheduler']


class NoScheduler(Scheduler):

    def __init__(self, config: dict, *args, **kwargs):
        """

        Parameters
        ----------
        config
        """
        super().__init__(config, *args, **kwargs)

# Register NoScheduler as a builder in the scheduler_factory
Scheduler.scheduler_factory.register('NoScheduler', NoScheduler)
