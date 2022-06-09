"""
Loads yaml configuration files as python objects

https://pyyaml.org/wiki/PyYAMLDocumentation
"""

import os

from uwtools.nice_dict import NiceDict
from uwtools.template import Template, TemplateConstants
from uwtools.yaml_file import YAMLFile

class Configure(NiceDict):

    """
        A class that reads a yaml file and checks the contents against a schema using the language
    """

    def __init__(self, config_file):
        super().__init__()
        self.source = os.path.abspath(config_file)
        if config_file is not None:
            config = self.load_yaml(config_file)
            if config is None:
                config = {}
            self.update(config)

    def load_yaml(self,config_file=None,data=None):
        if config_file is not None:
            config = YAMLFile(os.path.abspath(config_file))
        else:
            config = data
        config = Template.substitute_structure_from_environment(config)
        config = Template.substitute_structure( config, TemplateConstants.DOLLAR_PARENTHESES, self.get)
        config = Template.substitute_with_dependencies(config,config,TemplateConstants.DOLLAR_PARENTHESES,shallow_precedence=False)
        self.update(config)