from ..logger import Logger
from ..factory import create_factory


class Stage:

    logger = Logger(__name__)
    stage_factory = create_factory('Stage')

    def __init__(self, source, target, stage, *args):
        for action, info in stage.items():
            actor = self.stage_factory.create(action, *args)
            self.logger.info(f'processing: {action}')
            actor(info, source, target, self.logger)
