# --------------------------------------------------------------------------------
# Author: JCSDA
#
# --------------------------------------------------------------------------------
import os.path
from ..factory import create_factory
from .schema_validate import SchemaValidate

SchemaReaderFactory = create_factory('SchemaReader')


class SchemaReader(SchemaReaderFactory):
    cache = {}

    def __init__(self, schema_path, extension='yaml'):
        self._schema_path = schema_path
        self._extension = extension

    def read(self, name):
        if name in self.cache:
            return self.cache[name]

        filename = self.find_schema(name)
        if filename is not None:
            reader = SchemaReaderFactory.create(self._extension)
            # we take the first one, if more than one was found, we assume that
            # the first one is the one to use
            schema = reader.read(filename)
            for s in schema:
                self.cache[s['schema']] = s
                SchemaValidate.validate(s)
            if name not in self.cache:
                raise IndexError(f'Schema was not found: "{name}"')
            return self.cache[name]
        else:
            raise IndexError(f'Schema was not found: "{name}"')

    def find_schema(self, name):
        for path in self._schema_path:
            schema = os.path.join(path, f'{name}.{self._extension}')
            if os.path.exists(schema):
                return schema
        return None

    def schema_exists(self, name):
        return self.find_schema(name) is not None
