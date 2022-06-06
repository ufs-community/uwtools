# --------------------------------------------------------------------------------
# Author: JCSDA
#
# --------------------------------------------------------------------------------
from ..basic import to_list, no_list


class SchemaValidate(object):
    schema = {
        'schema': {
            'type': str,
            'required': True
        },
        'items': {
            'type': dict,
            'required': True
        },
        'ignore_unknown_keywords': {
            'type': bool,
            'required': False,
            'default': False
        },
        'help': {
            type: str,
            'required': False
        },
        'inherit': {
            'required': False,
            'unique': False
        },
        'merge': {
            # [ field1, field2, ... ]
            # the contents of the field should correspond
            # to the name of a schema in the schema directory
            'required': False,
            'unique': False
        }
    }

    item = {
        'required': {
            'required': False,
            'default': True,
            'type': bool,
            'show_in_help': True
        },
        'unique': {
            'required': False,
            'default': True,
            'type': bool,
            'show_in_help': True
        },
        'lowercase': {
            'required': False,
            'default': False,
            'type': bool,
            'show_in_help': False
        },
        'uppercase': {
            'required': False,
            'default': False,
            'type': bool,
            'show_in_help': False
        },
        'validate': {
            'required': False,
            'type': list,
            'show_in_help': True
        },
        'default': {
            'required': False,
            'show_in_help': True
        },
        'type': {
            'required': False,
            'show_in_help': True
        },
        'exclude_when': {
            'required': False,
            'show_in_help': True
        },
        'delete': {
            'required': False,
            'default': False,
            'show_in_help': False
        },
        'help': {
            'required': False,
            'show_in_help': False
        },
        'schema': {
            'required': False,
            'show_in_help': True
        },
        'excludes': {
            'required': False,
            'show_in_help': True,
            'type': list
        },
        'alias': {
            'required': False,
            'type': list,
            'show_in_help': True
        },
        'derived': {
            'required': False,
            'show_in_help': True
        },
        'category': {
            'required': False,
            'type': str
        }
    }

    @classmethod
    def validate(cls, other):
        # first make sure items are not None, we need an empty dict. This can happen
        # with YAML schemas in particular
        if 'items' in other:
            for k, item in other['items'].items():
                if item is None:
                    other['items'][k] = {}
        text = cls._validate(other, cls.schema)
        if 'items' in other:
            for k, item in other['items'].items():
                text += cls._validate(item, cls.item)
        if len(text) > 0:
            raise ValueError('Invalid schema definition %s' % '\n'.join(text))

    @classmethod
    def _validate(cls, other, what):
        text = []
        my_keys = set([x for x in what.keys()])
        other_keys = set(other.keys())
        if my_keys != other_keys:
            diff = my_keys.difference(other_keys)
            for d in diff:
                if what[d]['required']:
                    text.append('-- Missing keyword "%s" is required' % d)
            diff = other_keys.difference(my_keys)
            for d in diff:
                text.append('-- Invalid keyword "%s"' % d)
        # set defaults first
        for k in my_keys:
            if k not in other:
                if 'default' in what[k]:
                    other[k] = what[k]['default']
        for k in other_keys:
            if k in what:
                entry = other[k]
                schema = what[k]
                if 'type' in schema:
                    error = '-- Type error: %s[%s] should be of type %s' % (k, entry, schema['type'].__name__)
                    if schema['type'] == list:
                        other[k] = to_list(entry)
                    elif schema['type'] == dict:
                        if not isinstance(entry, dict):
                            text.append(error)
                    else:
                        try:
                            new = schema['type'](entry)
                            other[k] = new
                        except IndexError:
                            text.append(error)
                if 'unique' in what[k]:
                    if not what[k]['unique']:
                        other[k] = to_list(entry)
                    else:
                        other[k] = no_list(entry)
        return text
