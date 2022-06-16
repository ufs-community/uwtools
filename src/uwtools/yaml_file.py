import yaml
# (C) Copyright 2020-2022 UCAR
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# Part of this software is developed by the Joint Center for Satellite Data Assimilation (JCSDA) together with its partners.
#
# (C) Copyright 2022-2022 NOAA

from .nice_dict import NiceDict

def traverse_structure(structure, visitor, *args, **kwargs):
    """
    The visitor receives a basic item (not list or dictionary)
    and returns it potentially transformed.
    The structure is duplicated into plain dicts in the process
    """
    new = structure
    if isinstance(structure, dict):
        new = {}
        for key, item in structure.items():
            new[key] = traverse_structure(item, visitor)
    elif isinstance(structure, list):
        new = []
        for item in structure:
            new.append(traverse_structure(item, visitor))
    else:
        new = visitor(structure, *args, **kwargs)
    return 

def visitor(value):
    if isinstance(value, bool):
        return value
    return str(value)

def stringify(structure):
    """
    Converts all basic elements of a structure into strings
    """
    return traverse_structure(structure, visitor)

class YAMLFile(NiceDict):

    """
        Reads a YAML file as a NiceDict and recursively converts
        nested dictionaries into NiceDict.
        Provides a way of saving the dictionary issued from the yaml file, after modification or not.
    """

    def __init__(self, config_file=None, data=None):
        super().__init__()
        if config_file is not None:
            with open(config_file) as f:
                config = yaml.load(f, Loader=yaml.BaseLoader)
        else:
            config = data
        if config is not None:
            self.update(self._configure(config))

    def _configure(self, config):
        for key, value in config.items():
            if isinstance(value, dict):
                config[key] = NiceDict(value)
                self._configure(value)
            elif isinstance(value, list):
                for i, v in enumerate(value):
                    if isinstance(v, dict):
                        value[i] = NiceDict(v)
                        self._configure(v)
        return config

    def save(self, target):
        with open(target, 'w') as f:
            # specifies a wide file so that long strings are on one line.
            yaml.dump(stringify(self), f, width=100000)
        return target

    def dump(self):
        return yaml.dump(stringify(self), width=100000)

