"""
Loads yaml configuration files as python objects

https://pyyaml.org/wiki/PyYAMLDocumentation
"""

import os

from uwtools.nice_dict import NiceDict
from uwtools.loaders import load_yaml

from uwtools.template import Template, TemplateConstants

class Configure(NiceDict):

    """
        A class that reads a yaml file and checks the contents against all vaules for subsitutions
    """

    def __init__(self, config_file=None):
        super().__init__()
        if config_file is not None:
            config = self.include(os.path.abspath(config_file))
            if config is None:
                config = {}
        else:
            config = {}        
        self.update(config)
    
    # This method is the sample code needed to implement the !INCLUDE tag    
    def include(self,config_file=None,data=None):
        if config_file is not None:
            config = load_yaml(os.path.abspath(config_file))
        else:
            config = data
        config = Template.substitute_structure_from_environment(config)
        config = Template.substitute_structure( config, TemplateConstants.DOLLAR_PARENTHESES, self.get)
        config = Template.substitute_with_dependencies(config,config,TemplateConstants.DOLLAR_PARENTHESES,shallow_precedence=False)
        return(self.update(config))