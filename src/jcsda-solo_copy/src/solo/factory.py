# --------------------------------------------------------------------------------
# Author: JCSDA
#
# --------------------------------------------------------------------------------
import sys


class Factory(object):

    """
        A factory to hold classes under registered strings. Factory classes are generated
        automatically by the function createFactory. New classes are also added to the
        module's namespace so they become visible by importers.
        createFactory('Object') creates the class called ObjectFactory.
        There is no need to create an instance of the factory generated, all methods
        are class methods.
    """

    _members = {}
    _default = None
    _name = ''

    @classmethod
    def register(cls, name: str, what: object):
        cls._members[name] = what

    # if set, any unknown name will create one of those
    @classmethod
    def register_default(cls, what):
        cls._default = what

    @classmethod
    def create(cls, name: str, *args, **kwargs):
        if name not in cls._members:
            if cls._default is not None:
                return cls._default(*args, **kwargs)
            else:
                raise IndexError('%s "%s" is unknown, available: %s' %
                                 (cls._name, name, ', '.join(cls._members.keys())))
        return cls._members[name](*args, **kwargs)

    @classmethod
    def registered(cls):
        return set(cls._members.keys())

    @classmethod
    def is_registered(cls, name: str):
        return name in cls._members

    @classmethod
    def get_factory(cls, name: str):
        me = sys.modules[__name__]
        return getattr(me, name)


def create_factory(name: str):
    # this creates the factory class with the name <name>Factory where <name> is the
    # argument. Once it's created, the user can either:
    #   1. from factory import <name>Factory
    #   2. my_factory = Factory.get_factory('<name>Factory')
    # if using a python IDE, 1. is frowned upon because the name
    # if not visible in the namespace before runtime.
    me = sys.modules[__name__]
    name = '%sFactory' % name
    if not hasattr(me, name):
        setattr(me, name, type(name, (Factory,), {'_name': name, '_members': {}, '_default': None}))
    return getattr(me, name)
