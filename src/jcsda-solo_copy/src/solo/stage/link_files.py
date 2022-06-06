from ..file_manager import FileManager
from .directory import Directory


class LinkFiles(Directory):
    """
        Please see directory.py for syntax
    """

    def action(self, source, target_path, target_file, logger):
        logger.info(f'Linking {source} to {target_path}')
        FileManager.symlink(source, target_path)
