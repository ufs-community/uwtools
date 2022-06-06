import os
from ..yaml_file import YAMLFile
from ..file_manager import FileManager
from ..template import Template, TemplateConstants
from .directory import Directory


class TemplateFiles(Directory):
    """
        Please see directory.py for syntax.

        Inherits from Directory, but expects an extra entry:
        template:
            pattern: AT_SQUARE_BRACES | DOLLAR_PARENTHESES etc...
            dictionaries:
                - file1
                - file2
        dictionaries are expected to be yaml files. If a value in dictionary
        exists in more than one, the latest dictionary in the list has
        precedence.
    """

    def __init__(self, *args):
        super().__init__(*args)
        self._index = {}
        self._pattern = 'DOLLAR_PARENTHESES'

    def __call__(self, data, source, *args, **kwargs):
        if 'template' not in data:
            raise IndexError('A "template" section is expected')
        if 'pattern' in data['template']:
            self._pattern = data['template']['pattern']
        self._pattern = getattr(TemplateConstants, self._pattern)
        dictionary = self.read_dictionaries(source, data)
        self._index = Template.build_index(dictionary)
        super().__call__(data, source, *args, **kwargs)

    def action(self, source, target_path, target_file, logger):
        if not len(target_file):
            target_file = os.path.basename(source)
        target = os.path.join(target_path, target_file)
        logger.info(f'Copying {source} to {target}')
        FileManager.copy_transform(source, target, self.substitute)

    def substitute(self, text):
        return Template.substitute_string(text, self._pattern, self._index.get)

    @staticmethod
    def read_dictionaries(source, data):
        """
            Not particularly pretty, define this method so it can be overridden by sub-classes so they don't have
            to implement the logic again. There must be a better way, time is short.
        """
        if 'dictionaries' not in data['template']:
            raise IndexError('A "dictionaries" section is expected in "template"')
        dictionary = {}
        for d in data['template']['dictionaries']:
            c = YAMLFile(os.path.join(source, d))
            dictionary.update(c)
        return dictionary
