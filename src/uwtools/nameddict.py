# (C) Copyright 2020-2022 UCAR
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.

#
# NamedDict - A Dictionary that exposes its keys as attributes.
#

import collections.abc as abc

__all__ = ['NamedDict']


class NamedDict(abc.Mapping):
    def __init__(self, d=None):
        if d is None:
            object.__setattr__(self, '_NamedDict__dict', dict())
        else:
            object.__setattr__(self, '_NamedDict__dict', d)

    # Dictionary-like access / updates
    def __getitem__(self, name):
        # try:
        value = self.__dict[name]
        if isinstance(value, NamedDict):
            return value
        if isinstance(value, abc.Mapping):
            return NamedDict(value)
        if isinstance(value, abc.MutableSequence):
            return [NamedDict(v) if isinstance(v, abc.Mapping) and not isinstance(v, NamedDict)
                    else v for v in value]
        return value

    def __contains__(self, name):
        return name in self.__dict

    def __setitem__(self, name, value):
        self.__dict[name] = value

    def __delitem__(self, name):
        del self.__dict[name]

    def __len__(self):
        return len(self.__dict)

    def __iter__(self):
        return iter(self.__dict)

    def __getattr__(self, name):
        if name in self.__getattribute__('_NamedDict__dict'):
            return self[name]
        else:
            return getattr(self.__getattribute__('_NamedDict__dict'), name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        del self[name]

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.__dict)

    def __str__(self):
        return str(self.__dict)

    def get_dict(self):
        return self.__dict
