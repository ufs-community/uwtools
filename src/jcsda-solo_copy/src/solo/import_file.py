import sys
import os
import importlib
from pathlib import PurePath
from .basic_files import directory_list


class ImportFile:

    """
        Does a dynamic import of a module (either a directory or a file in a package).
    """

    @staticmethod
    def find_object(class_name, path):
        the_class = None
        file_list = directory_list(path, 'py')
        sys.path.insert(0, path)
        for py_file in file_list:
            # if filename.py, stem returns filename
            name = PurePath(py_file).stem
            module = importlib.import_module(name)
            try:
                the_class = getattr(module, class_name)
            except AttributeError:
                pass
            else:
                # <-----  stop as soon as we find it
                break
        sys.path.pop(0)
        return the_class

    @staticmethod
    def import_module(path):
        sys.path.insert(0, os.path.dirname(path))
        name = PurePath(path).stem
        module = importlib.import_module(name)
        sys.path.pop(0)
        return module
