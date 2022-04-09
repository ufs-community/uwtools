from ..factory import Factory


class Scheduler:

    scheduler_factory = Factory('Scheduler')

    _directive = ''

    def __init__(self, *args, **kwargs):
        pass

    def echo(self):
        print(f'Base directive is {self._directive}')
