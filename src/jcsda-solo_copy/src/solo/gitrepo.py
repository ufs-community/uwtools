from git import Repo  # git is part of GitPython: https://pypi.org/project/GitPython/


class GitRepo:

    """
        Implements some very basic functions on Git repos.
    """

    def __init__(self, destination_directory):
        self.target_dir = destination_directory
        self._repo = Repo.init(destination_directory, bare=False)

    def clone(self, url, destination, branch=None, tag=None):
        extra = {}
        if branch is not None:
            extra['b'] = branch
        elif tag is not None:
            extra['b'] = tag
        return self._repo.clone_from(url, destination, **extra)

    def pull(self):
        self._repo.remotes.origin.pull()
