import os
from pathlib import PurePath
from ..logger import SilentLogger
from ..file_manager import FileManager
from .base import Base


class CopyTree(Base):
    """
        Copies the contents of a directory tree into another one. The copy is recursive.
        The expected dictionary (data) is as follows:
            directories:  # list pairs (lists or tuple)
                - [source1, destination1]
                - [source2, destination2]
                - ...
                - [sourceN, destinationN]
            exclude:
                - filename1
                - filename2
                - ...
                - filenameN
        Copies all files in sourceN into destinationN skipping filenames in excludes.
    """
    def __call__(self, data, source, target, logger=SilentLogger()):
        """
           source and target are the root directories, if specified, the directories
           in data are considered to be relative to those.
        """
        exclude = set(data.get('exclude', []))
        count = 0
        for file_group in data['directories']:
            source_dir = os.path.join(source, file_group[0])
            root = self.find_root(source_dir)
            target_dir = os.path.join(target, file_group[1])
            for root, path, filename in FileManager.tree(root):
                print(root, path, filename)
                if filename not in exclude:
                    p = os.path.join(root, path, filename)
                    if (source_dir == root) or PurePath(os.path.join(root, path, filename)).match(source_dir):
                        q = os.path.join(target_dir, path, filename)
                        FileManager.makedirs(os.path.join(target_dir, path), exist_ok=True)
                        logger.info(f'Copying {p} to {q}')
                        FileManager.copy(p, q)
                        count += 1
            plural = ''
            if count:
                plural = 's'
            logger.info(f'{count} file{plural} copied')
