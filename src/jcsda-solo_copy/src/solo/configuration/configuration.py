import os
import yaml
from ..nice_dict import NiceDict
from ..language import stringify
from ..language.language import Language
from ..template import Template


class Configuration(NiceDict):

    """
        A class that reads a yaml file and checks the contents against a schema using the language
    """

    def __init__(self, config_file, schema_path='.', schema_name=None, environment=False):
        super().__init__()
        self.source = os.path.abspath(config_file)
        with open(config_file) as f:
            config = yaml.load(f, Loader=yaml.BaseLoader)
            if config is None:
                config = {}
            if environment:
                config = Template.substitute_structure_from_environment(config)
            if schema_name is not None:
                language = Language(schema_name, schema_path)
                new = language.validate(config)
                self.update(new)
            else:
                self.update(config)

    def save(self, overwrite=False, target_dir=None, target_name=None):
        """
            1. overwrite==True, overwrites the initial file
            2. overwrite==False, target_dir=None: error
            3. overwrite==True, target_dir==dir, target_name==None:
               saves dir/original name
            4. overwrite==True, target_dir==dir, target_name==name:
               saves dir/name
        """
        if overwrite:
            target_path = self.source
        elif target_dir is None:
            raise ValueError('if overwrite is False, needs a target_path')
        else:
            target_dir = os.path.abspath(target_dir)
            if target_name is None:
                target_name = os.path.basename(self.source)
            target_path = os.path.join(target_dir, target_name)
            if self.source == target_path:
                raise ValueError('won\'t overwrite with overwrite=False')
        with open(target_path, 'w') as f:
            # specifies a wide file so that long strings are on one line.
            yaml.dump(stringify(self), f, width=100000)
        return target_path

    def path(self):
        return os.path.dirname(self.source)

    def filename(self):
        return os.path.basename(self.source)

