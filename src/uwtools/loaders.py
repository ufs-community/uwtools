"""
Loads yaml configuration files as python objects

https://pyyaml.org/wiki/PyYAMLDocumentation
"""
import os
import collections
import pathlib
from typing import Any, Dict

from uwtools.yaml_file import YAMLFile

class Config(collections.UserDict):
    def __getattr__(self, name):
        return self.__dict__["data"][name]

def load_yaml(config_file: pathlib.Path):
    if config_file is not None:
        config = YAMLFile(os.path.abspath(config_file))
        if config is None:
            config = {}
    return config