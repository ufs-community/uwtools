"""
Loads yaml configuration files as python objects

https://pyyaml.org/wiki/PyYAMLDocumentation
"""

import collections
import pathlib
from typing import Any, Dict
from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


class Config(collections.UserDict):
    def __getattr__(self, name):
        return self.__dict__["data"][name]


def load_yaml(_path: pathlib.Path):
    with open(_path, "r") as _file:
        props = load(_file, Loader=Loader)
        return Config(props)
