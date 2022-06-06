from .language import Language
from ..nice_dict import NiceDict


class Directive(NiceDict):

    def __init__(self, schema_path, schema_format='yaml', schema_name=None, *args, **kwargs):
        self._schema_path = schema_path
        self._schema_format = schema_format
        super(Directive, self).__init__(*args, **kwargs)
        if schema_name:
            self._schema = schema_name
        elif hasattr(self, '__schema__'):
            self._schema = self.__schema__
        else:
            self._schema = self.__class__.__name__.lower()
        self.validate()

    def validate(self):
        language = Language(self._schema, schema_path=self._schema_path, extension=self._schema_format)
        for k, i in self.items():
            if isinstance(i, Directive):
                i.validate()
        new = language.validate(self)
        self.clear()
        self.update(new)

    def __str__(self):
        return self._schema + '\n' + super().__str__()

