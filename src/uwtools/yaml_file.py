'''
Class for managing YAML files with inline and envitionmenti
variable substituion with file inclustion support
'''
# (C) Copyright 2020-2022 UCAR
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# Part of this software is developed by the Joint Center for
# Satellite Data Assimilation (JCSDA) together with its partners.

import os
import yaml
from uwtools.template import Template, TemplateConstants
from .nice_dict import NiceDict

class YAMLFile(NiceDict):

    """
        Reads a YAML file as a NiceDict and recursively converts
        nested dictionaries into NiceDict.
        Provides a way of saving the dictionary issued from the yaml file,
        after modification or not.
    """

    def __init__(self, config_file=None, data=None):
        super().__init__()
        if config_file is not None:
            config = self.include(config_file=os.path.abspath(config_file))
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
                for i, var in enumerate(value):
                    if isinstance(var, dict):
                        value[i] = NiceDict(var)
                        self._configure(var)
        return config

    def include(self,config_file=None,data=None,replace_realtime=False):
        ''' Sample code needed to implement the !INCLUDE tag '''
        if config_file is not None:
            with open(config_file,encoding='utf-8') as _file:
                config = NiceDict(yaml.load(_file, Loader=yaml.Loader))
        else:
            config = data
        config = Template.substitute_structure_from_environment(config)
        config = Template.substitute_structure(config,TemplateConstants.DOLLAR_PARENTHESES,self.get)
        if replace_realtime is True:
            config = Template.substitute_structure(config,
                     TemplateConstants.DOUBLE_CURLY_BRACES,self.get)
        config = Template.substitute_with_dependencies(config,config,
                 TemplateConstants.DOLLAR_PARENTHESES,shallow_precedence=False)
        return self.update(config)
