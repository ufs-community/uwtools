__all__ = ['Factory']


class Factory:
    '''
    General Purpose Object Factory (Factory) to create all kinds of objects.
    It provides methods to register a Builder and create concrete object
    instances based on key value.
    It also provides methods to check if a Builder is registered as well as
    all the registered builders in the Factory.
    '''

    def __init__(self, name: str):
        '''
        Initialize the Factory and its Builders
        '''
        self._name = f'{name}Factory'
        self._builders = {}

    def register(self, key: str, builder: object):
        '''
        Register a new builder in the Factory
        '''
        if self.is_registered(key):
            print(f'{key} is already a registered Builder in {self._name}')
            return
        self._builders[key] = builder

    def create(self, key: str, *args, **kwargs):
        '''
        Instantiate a registered Builder
        '''
        if not self.is_registered(key):
            raise KeyError(
                f"{key} is not a registerd builder in {self._name}.\n" +
                "Available builders are:\n" +
                f"{', '.join(self._builders.keys())}")

        return self._builders[key](*args, **kwargs)

    def destroy(self, key: str):
        '''
        Retire a registered builder from the Factory
        Note: This will not delete the instance if it was created, just that
        this Builder will no longer be able to work in the Factory
        '''
        try:
            del self._builders[key]
        except KeyError:
            print(f'{key} is not a registered Builder in {self._name}')

    def registered(self):
        '''
        Return a set of all registered builders in the Factory
        '''
        return set(self._builders.keys())

    def is_registered(self, key: str):
        '''
        Return True/False if a builder is registered in the Factory
        '''
        return key in self._builders.keys()
