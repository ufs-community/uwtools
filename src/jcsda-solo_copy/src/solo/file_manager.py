from .files import file_factory


class FileManager:

    """
        Copy files from source to target. File path needs to be prefixed with
        a protocol in the form protocol://
        Copiers in the module are instantiated depending on combinations of systems.
        Supported, at the time of writing:
           file:// -> file://
           file:// -> s3://
           s3:// -> file://
           s3:// -> s3://
           If a protocol is unknown, file:// -> file:// is assumed.

        The "progress" argument is a function / method called before executing a copy,
        it receives the source full path and the target full path. It returns a value:
        - either the target passed
        - the target renamed, or with a different directory structure
    """

    default = 'file'

    @classmethod
    def copy(cls, source, target, progress=None):
        """
            Copies a file from source to destinations, both source and target
            need to be prefixed: file:// or s3://
        """
        copier, source, target = cls._create_copier(source, target)
        copier.copy(source, target, progress=progress)

    @classmethod
    def copy_transform(cls, source, target, transform, load_all=True, **kwargs):
        """
            Copies the file. Expects a text file. transform is called either for the
            whole contents of the files (load_all=True) or line by line (load_all=False)
            The signature for transform is:
            def transform(text, **kwargs):
                # do that you want
                return text
            **kwargs are passed as received by this method
        """
        copier, source, target = cls._create_copier(source, target)
        copier.copy_transform(source, target, transform, load_all=load_all, **kwargs)

    @classmethod
    def copy_tree(cls, source, target, progress=None):
        """
            Copies a full tree of directories / files
        """
        copier, source, target = cls._create_copier(source, target)
        copier.copy_tree(source, target, progress)

    @classmethod
    def tree(cls, path):
        """
            Traverses a directory structure in depth.
        """
        path = cls.add_default_prefix(path)
        prefix, path = cls.protocol_path(path)
        actor = file_factory.create(prefix)
        return actor.tree(path)

    @classmethod
    def dir(cls, path):
        """
            Lists the contents of a directory. Return a three value tuple:
            filename: str, full_path+filename: str, is_a_file: bool)
        """
        path = cls.add_default_prefix(path)
        prefix, path = cls.protocol_path(path)
        actor = file_factory.create(prefix)
        return actor.dir(path)

    @classmethod
    def file_exists(cls, path):
        path = cls.add_default_prefix(path)
        prefix, path = cls.protocol_path(path)
        actor = file_factory.create(prefix)
        return actor.file_exists(path)

    @classmethod
    def makedirs(cls, path, exist_ok=False):
        path = cls.add_default_prefix(path)
        prefix, path = cls.protocol_path(path)
        actor = file_factory.create(prefix)
        actor.makedirs(path, exist_ok=exist_ok)

    @classmethod
    def symlink(cls, source, target):
        source = cls.add_default_prefix(source)
        prefix, source = cls.protocol_path(source)
        actor = file_factory.create(prefix)
        actor.symlink(source, target)

    @staticmethod
    def protocol_path(path):
        """
            In a string protocol://path, returns protocol and path separately
        """
        parts = path.split('://')
        if len(parts) == 1:
            parts = ['file', parts[0]]
        return parts[0], parts[1]

    @staticmethod
    def add_prefix(path, prefix):
        """
            prepends prefix:// to the string path
        """
        parts = path.split('://')
        if len(parts) == 1:
            path = '://'.join((prefix, path))
        return path

    @classmethod
    def add_default_prefix(cls, path):
        """
            prepends the default prefix to the string path
        """
        parts = path.split('://')
        if len(parts) == 1:
            # assume it's a local file
            path = '://'.join((cls.default, path))
        return path

    @classmethod
    def _create_copier(cls, source, target):
        # if the files don't have a protocol (protocol://) we add a default one: file://
        source = cls.add_default_prefix(source)
        target = cls.add_default_prefix(target)
        source_prefix, source_path = cls.protocol_path(source)
        target_prefix, target_path = cls.protocol_path(target)
        try:
            copier = file_factory.create(source_prefix + '_' + target_prefix)
        except IndexError:
            raise ValueError(f'Unknown protocol or typo in either {source} or {target}')
        else:
            return copier, source_path, target_path
