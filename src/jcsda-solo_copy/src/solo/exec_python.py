import importlib
import builtins
import copy
from .nice_dict import NiceDict


class ExecPython:

    """
        This is designed to execute Python expressions in a dictionary, most likely coming from a YAML file. The general
        structure should be:
        config = {
           'field1': ...,
           'field2': ...,
           'field3': ...,
           'field4': {
               'f1': 'python statement(s)
               'f2': 'python statement(s)
               'f3': 'not python
           }
           'type_field': {
               'field1': 'int'
               'field2': solo.date.JediDate
               'field3': solo.date.DateIncrement
               'f1': 'int'
           }
        }
        ExecPython(config, ['field4'], 'type_field')
        config is modified in place with the results of the evaluation of the python statements.

        Multi-line python code is not supported (not sure it's necessary, more complicated to implement
        and a bit more dangerous security-wise).

        The "type" dictionary describes how to type the fields in config before calling the python code. Results
        are converted to string by default, unless specified in the "type" dictionary (e.g. 'f1').

        Please see tests/test_exec_python.py
    """

    def __init__(self, config, exec_list, type_field_name=None):
        for where in exec_list:
            config = copy.copy(config)
            variables = config
            if type_field_name is not None:
                types = self.build_path(where, type_field_name)
                type_dict = NiceDict.reach_attribute(config, types)
                variables = self.create_variables(config, type_dict)
            else:
                type_dict = {}
            for field, python in NiceDict.reach_attribute(config, where).items():
                if field != type_field_name:
                    result = self.execute(python, variables)
                    if field in type_dict:
                        result = self.get_class(type_dict[field])(result)
                    else:
                        result = str(result)
                    NiceDict.assign_value(config, self.build_path(where, field), result)

    @staticmethod
    def execute(expression, variables):
        # we return the expression if python error
        try:
            return eval(expression, variables, variables)
        except Exception as e:  # deliberate catch all
            print(e)
            return expression

    @classmethod
    def create_variables(cls, config, types):
        # instantiate objects whenever needed
        for item_name, item_type in types.items():
            if item_name in config:
                config[item_name] = cls.get_class(item_type)(config[item_name])
        return config

    @staticmethod
    def get_class(item_type):
        parts = item_type.split('.')
        item_module = '.'.join(parts[:-1])
        item_class = parts[-1]
        # if no module specified, assume builtins
        module = builtins
        if len(item_module):
            module = importlib.import_module(item_module)
        return getattr(module, item_class)

    @staticmethod
    def build_path(path, field_name):
        return '.'.join((path, field_name))
