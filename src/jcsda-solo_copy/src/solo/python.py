import os
import importlib
import inspect


def instantiate_class_from_module(module_name, class_name, *args, **kwargs):
    """
        loads the module module_name and instantiates class_name that is
        supposed to be in the module.
        examples for module_name: 'drivers' or 'drivers.network'
    """
    module = importlib.import_module(module_name)
    _class = getattr(module, class_name)
    return _class(*args, **kwargs)


def load_classes_from_module(module_name):
    """
        Loads all the python files in a module directory and indexes each
        of the classes found in each file.
    """
    dir_name = module_name.replace('.', '/')
    files = [x.replace('.py', '') for x in os.listdir(dir_name) if x.find('.py') != -1]
    classes = {}
    for file_name in files:
        current_module = f'{module_name}.{file_name}'
        module = importlib.import_module(current_module)
        members = inspect.getmembers(module)
        for name, obj in members:
            if inspect.isclass(obj) and obj.__module__ == current_module:
                # ignoring potential duplicates
                classes[name] = obj
    return classes
