from ..factory import Factory
from .copy_files import CopyFiles
from .link_files import LinkFiles
from .copy_tree import CopyTree
from .template_files import TemplateFiles
from .stage import Stage


class DoNothing:

    def __call__(self, *args, **kwargs):
        pass


# StageFactory is created in stage.py
stage_factory = Factory.get_factory('StageFactory')
stage_factory.register('copy_files', CopyFiles)
stage_factory.register('link_files', LinkFiles)
stage_factory.register('copy_tree', CopyTree)
stage_factory.register('template_files', TemplateFiles)
# we accept any keyword so that the user can add information in the file
# that we ignore.
stage_factory.register_default(DoNothing)
