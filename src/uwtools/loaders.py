#pylint: disable=missing-class-docstring,missing-function-docstring
"""
Loads yaml configuration files as python objects

Developer Notes:

Prior to this update load_yaml returned a Config object
but we have not developed the use case for such a Class

Here we have changed load_yaml to a simple function call because
the UserDict overloaded __getattr__ for dot resolution is now in the
YAMLFile class that inherits UserDict

https://pyyaml.org/wiki/PyYAMLDocumentation
"""
import os
import collections
import pathlib

from uwtools.yaml_file import YAMLFile

class Config(collections.UserDict):
    '''Config Class embeded in loader fuction (TODO: not used)'''
    def __getattr__(self, name):
        return self.__dict__["data"][name]

def load_yaml(config_file: pathlib.Path):
    '''Function for reading YAML files that supports concatenation'''
    if config_file is not None:
        config = YAMLFile(os.path.abspath(config_file))
    else:
        config = collections.UserDict()
    return config
