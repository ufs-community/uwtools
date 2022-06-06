import os
import shutil
from ..basic_files import tree


class FileFile:

    @staticmethod
    def copy(source: str, target: str, progress=None):
        if progress:
            target = progress(source, target)
        target_path = os.path.dirname(target)
        if len(target_path):
            os.makedirs(target_path, exist_ok=True)
        shutil.copy(source, target)

    @staticmethod
    def copy_transform(source, target, transform, load_all, **kwargs):
        target_path = os.path.dirname(target)
        if len(target_path):
            os.makedirs(target_path, exist_ok=True)
            with open(source) as f:
                with open(target, 'w') as g:
                    if load_all:
                        lines = ''.join(f.readlines())
                        lines = transform(lines, **kwargs)
                        g.write(lines)
                    else:
                        line = f.readline()
                        while line:
                            line = transform(line, **kwargs)
                            g.write(line)
                            line = f.readline()

    @classmethod
    def copy_tree(cls, source, target, progress=None):
        for source, path, file in tree(source):
            source_path = os.path.join(source, path, file)
            target_path = os.path.join(target, path, file)
            cls.copy(source_path, target_path, progress)
