import os
from ..basic_files import tree


class File:

    @staticmethod
    def file_exists(path):
        if '~' in path:
            path = path.replace('~', os.path.expanduser('~'))
        path = os.path.abspath(path)
        return os.path.exists(path)

    @staticmethod
    def makedirs(path, exist_ok=False):
        os.makedirs(path, exist_ok=exist_ok)

    @staticmethod
    def symlink(source, target):
        if target[-1] == '/':
            os.makedirs(target, exist_ok=True)
            target = os.path.join(target, os.path.basename(source))
        os.symlink(source, target)

    @staticmethod
    def tree(path):
        return tree(path)

    @staticmethod
    def dir(path):
        files = os.listdir(path)
        for filename in files:
            directory = os.path.join(path, filename)
            yield filename, directory, os.path.isfile(directory)
