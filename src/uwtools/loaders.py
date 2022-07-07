#pylint: disable=missing-class-docstring,missing-function-docstring
"""
Loads yaml configuration files as python objects

Developer Notes:

Prior to this update load_yaml returned a Config object
but we have not developed the use case for such a Class

Here we have changed load_yaml to a simple function call because
returning Config(config) in it's previous incarnation did not work with
the YAML parsing extensions as it return a Class Object before it was needed.
For now we have moved the specifics of the YAML extensions into configure.py Configure Class
for containment as we begin to develop a Configuration Manager

Note: it's just a function and the Class Object is left here for historical reason as
it used to use UserDict from collections and we are now using NiceDict

https://pyyaml.org/wiki/PyYAMLDocumentation
"""
import os
import collections
import pathlib

from uwtools.yaml_file import YAMLFile
from uwtools.nice_dict import NiceDict

class Config(collections.UserDict):
    '''Config Class embeded in loader fuction (TODO: not used)'''
    def __getattr__(self, name):
        return self.__dict__["data"][name]

def load_yaml(config_file: pathlib.Path):
    '''Function for reading YAML files that supports concatenation'''
    if config_file is not None:
        config = YAMLFile(os.path.abspath(config_file))
    else:
        config = NiceDict()
    return config
