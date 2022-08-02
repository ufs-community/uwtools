"""
Configure Class for using Jinja2 Templating Framework
"""

import pathlib

from jinja2 import Environment, FileSystemLoader, meta
from uwtools.yaml_file import YAMLFile

class Jinja2Config(YAMLFile):
    '''Name List Configure Class to support Name List Generation Utility Code'''
    def __init__(self, template_file=None, config_file=None):
        '''instantiate Jinja2 environment and set template input from files top of the filesystem'''
        super().__init__()
        self.j2env=Environment(loader=FileSystemLoader(searchpath='/'),
                               trim_blocks=True,lstrip_blocks=True)
        if config_file is not None:
            self.yaml_config = YAMLFile(config_file=config_file)
        else:
            self.yaml_config = None
        if template_file is not None:
            self.template_file = template_file
            self.template = self.load_j2_template(template_file)
        else:
            self.template = None
        self.meta = meta

    def load_j2_template(self, _file: pathlib.Path):
        '''load jinja2 template file for a nl specific name list'''
        self.template= self.j2env.get_template(_file)
        return self.template
