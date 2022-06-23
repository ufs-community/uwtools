#pylint: disable=missing-class-docstring,missing-function-docstring
"""
Loads yaml configuration files as python objects

https://pyyaml.org/wiki/PyYAMLDocumentation
"""

import collections
import pathlib
from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class Config(collections.UserDict):
    def __getattr__(self, name):
        return self.__dict__["data"][name]


def load_yaml(_path: pathlib.Path):
    #pylint: disable=unspecified-encoding
    with open(_path, "r") as _file:
        props = load(_file, Loader=Loader)
        return Config(props)
