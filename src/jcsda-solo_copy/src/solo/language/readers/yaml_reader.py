# --------------------------------------------------------------------------------
# Author: JCSDA
#
# --------------------------------------------------------------------------------
import yaml
from ..schema_reader import SchemaReader
from ...logger import Logger


class YAMLReader(object):

    logger = Logger(__name__)

    @staticmethod
    def read(filename):
        with open(filename) as f:
            try:
                schema = yaml.load(f, Loader=yaml.FullLoader)
            except Exception as e:
                YAMLReader.logger.error(f'Error reading: {filename}')
                raise
            if not isinstance(schema, list):
                schema = [schema]
            return schema


SchemaReader.register('yaml', YAMLReader)
