from .scheduler import Scheduler

__all__ = ['PBS']


class PBS(Scheduler):

    _directive = '#PBS'

    def __init__(self, config: dict):

        self._config = config

    def echo(self):
        print(f'PBS directive is {self._directive}')


# Register PBS as a builder in the scheduler_factory
Scheduler.scheduler_factory.register('PBS', PBS)
