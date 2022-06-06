# --------------------------------------------------------------------------------
# Author: JCSDA
#
# --------------------------------------------------------------------------------
import copy
from ..basic import to_list, no_list, is_sequence_and_not_string
from ..logger import Logger
from .schema_reader import SchemaReader
from .validate import Validate
from .types import Types
from .ordered_combinations import OrderedCombinations


class Language(object):

    """
        Validates 'requests', key value pairs in dictionaries against a schema definition
        contained in a dictionary also.
        Dictionaries are regularly copied (copy.deepcopy) to avoid side-effect of modifying
        dictionaries that could be cached in memory.
    """

    logger = Logger(__name__)

    def __init__(self, schema_name, schema_path=None, extension='yaml'):
        self._schema_path = to_list(schema_path)
        self._extension = extension
        self._name = schema_name
        self._schema = None
        self._schema_reader = SchemaReader(self._schema_path, extension)

    def validate(self, request):
        """
            This is where the magics happens.
        """
        try:
            # prepare_schema loads and merges inherited schemas if relevant.
            schema_meta, self._schema = self.prepare_schema(self._name, request)
            request = self.resolve_aliases(request, self._schema)
            s = self._schema
            s_keys = set(s.keys())
            r_keys = set(request.keys())

            # if the request has keywords which are not in the schema, we
            # shutdown straight away
            if not schema_meta['ignore_unknown_keywords']:
                if not s_keys.issuperset(r_keys):
                    raise ValueError('Unknown keyword(s) in %s: %s'
                                     % (self._name, ', '.join(r_keys.difference(s_keys))))

            # if the request does not have keywords which are required, we also
            # shutdown straight away (they could have a default value though
            # in that case we assign them).
            required = []
            for key in s_keys.difference(r_keys):
                if s[key]['required']:
                    required.append(key)

            if len(required) > 0:
                remaining = []
                for key in required:
                    if 'default' in s[key]:
                        request[key] = s[key]['default']
                    else:
                        remaining.append(key)
                if len(remaining) > 0:
                    raise ValueError(f'Required keyword(s) are missing in {self._name}: {", ".join(remaining)}')

            # deal with lists and non-lists and spot the categories
            categories = []
            for k, i in request.items():
                if k in s:
                    if s[k]['unique']:
                        if is_sequence_and_not_string(i) and len(i) > 1:
                            raise ValueError('In %s, the keyword "%s" allows one value, not a list' % (self._name, k))
                        request[k] = no_list(i)
                    else:
                        request[k] = to_list(i)
                        if len(request[k]) == 0 and s[k]['required']:
                            raise ValueError('In %s, the keyword "%s" cannot be an empty list' % (self._name, k))
                    # also expand sub-schemas
                    if 'schema' in s[k]:
                        sub_schema = s[k]['schema']
                        lang = Language(sub_schema, schema_path=self._schema_path, extension=self._extension)
                        i = to_list(i)
                        for index, entry in enumerate(i):
                            i[index] = lang.validate(entry)
                    if 'category' in s[k]:
                        categories.append(s[k]['category'])

            for category in categories:
                request['__' + category] = []
            # now a pass over all the elements of the request
            for k, i in request.items():
                if k in s:
                    if 'type' in s[k]:
                        request[k] = self.create_type(s[k]['type'], request[k])

                    if s[k]['lowercase']:
                        request[k] = self.to_lowercase(s[k], request[k])

                    if s[k]['uppercase']:
                        request[k] = self.to_uppercase(s[k], request[k])

                    if 'validate' in s[k]:
                        assert(Validate.is_registered(s[k]['validate'][0]))
                        f = Validate.create(s[k]['validate'][0], *s[k]['validate'][1:])
                        request[k] = f(k, request)

                    if 'category' in s[k]:
                        key = '__' + s[k]["category"]
                        request[key].append(k)

        except ValueError as e:
            self.logger.error('')
            raise SystemExit(e)

        return request

    def expand_schema(self, schema, request):
        _, schema = self.prepare_schema(schema, request)
        return schema

    def partial_request_validate(self, request):

        # prepare_schema loads and merges inherited schemas if relevant.
        schema_meta, self._schema = self.prepare_schema(self._name, request)
        s = self._schema

        # give a chance to the user to run through the request
        # now that it has been processed and validated.

        return request, schema_meta

    @staticmethod
    def create_type(type_name, value):
        """
            Instantiates types using the Type factory (types.py)
        """
        if is_sequence_and_not_string(value):
            result = []
            for v in value:
                result.append(Types.create(type_name, v))
            return result
        return Types.create(type_name, value)

    @staticmethod
    def to_lowercase(attributes, value):
        if is_sequence_and_not_string(value):
            result = []
            for v in value:
                result.append(v.lower())
            return result
        return value.lower()

    @staticmethod
    def to_uppercase(attributes, value):
        if is_sequence_and_not_string(value):
            result = []
            for v in value:
                result.append(v.upper())
            return result
        return value.upper()

    def prepare_schema(self, schema_name, request):
        """
            Deals with inheritance and merging. This is a recursive
            process
        """
        schema = self._schema_reader.read(schema_name)
        schema_meta, schema = self.split_schema(schema)
        schema = self.handle_inheritance(schema_meta, schema, request)
        schema = self.handle_merge(schema_meta, schema, request)
        excludes = {}
        for k, i in schema.items():
            if 'alias' in i:
                schema[k]['alias'] = set(i['alias'])
            if 'exclude_when' in i:
                excludes[k] = i['exclude_when']
        schema = self.evaluate_excludes(excludes, schema, request)
        return schema_meta, schema

    @staticmethod
    def evaluate_excludes(excludes, schema, request):
        # declare all keys value pair of the dictionary
        # as local variables
        for k, i in request.items():
            locals()[k] = i
        for key, expression in excludes.items():
            if eval(expression):
                del(schema[key])
        return schema

    @staticmethod
    def split_schema(schema):
        """
            splits the schema meta data and the schema for keywords (called items).
        """
        schema_meta = {}
        for k, i in schema.items():
            if k != 'items':
                schema_meta[k] = i
        return schema_meta, copy.deepcopy(schema['items'])

    def handle_inheritance(self, schema_meta, schema, request):
        """
            merges the current schema with the schema from the parent(s)
        """
        if 'inherit' in schema_meta:
            schema = copy.deepcopy(schema)
            parents = schema_meta['inherit']
            for parent in parents:
                parent_meta, parent = self.prepare_schema(parent, request)
                schema = self.inherit(schema, parent)
        return schema

    def handle_merge(self, schema_meta, schema, request):
        """
            merges the current schema with the schema from the parent(s)
            the parent's names are defined in fields of the request
        """
        if 'merge' in schema_meta:
            schema = copy.deepcopy(schema)
            schema_list = []
            for item in schema_meta['merge']:
                schema_name = None
                if item in request:
                    schema_name = request[item]
                elif item in schema and 'default' in schema[item]:
                    schema_name = str(schema[item]['default'])
                if schema_name is not None:
                    schema_list.append(schema_name)
            schemas = OrderedCombinations.find_schemas(schema_list, self._schema_reader)
            if schemas is not None:
                for schema_name in schemas:
                    schema_meta, other = self.prepare_schema(schema_name, request)
                    schema = self.inherit(other, schema)
        return schema

    @staticmethod
    def inherit(me, parent):
        """
            adds to me everything that is the parent and not in me
        """
        delete = []
        for k, i in parent.items():
            if k not in me:
                me[k] = i
            else:
                if me[k]['delete']:
                    delete.append(k)
                else:
                    for kk, ii in i.items():
                        if kk not in me[k]:
                            me[k][kk] = ii
        for k in delete:
            del(me[k])
        return me

    @staticmethod
    def resolve_aliases(request, s):
        def find_original(s, value):
            for k, i in s.items():
                if 'alias' in i:
                    if value in i['alias']:
                        return k
            return value

        if isinstance(request, dict):
            result = {}
            for k, i in request.items():
                if k not in s:
                    result[find_original(s, k)] = i
                else:
                    result[k] = i
            return result
        else:
            return request
