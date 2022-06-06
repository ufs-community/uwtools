# --------------------------------------------------------------------------------
# Author: JCSDA
#
# --------------------------------------------------------------------------------
from ..factory import create_factory
from ..basic import to_list

ValidationFactory = create_factory('Validation')


class Validate(ValidationFactory):
    pass


class ValidateSetChoice(object):
    def __init__(self, *args):
        self._values = set(args)

    def __call__(self, keyword, request):
        value = request[keyword]
        values = to_list(value)
        for v in values:
            if v not in self._values:
                raise ValueError('For keyword "%s", value "%s" is not valid, available choices: %s' % (
                    keyword, v, ', '.join(self._values)))
        return value


class ValidateExclude(object):
    def __init__(self, *args):
        self._values = list(args)

    def __call__(self, keyword, request):
        count = 0
        keywords = self._values + [keyword]
        for value in keywords:
            if value in request and request[value] is not None:
                count += 1
        if count != 1:
            raise ValueError('Keywords %s are exclusive, at least one and only one of them should be defined' % (
                ', '.join(keywords)))
        for k in keywords:
            if k in request and request[k] is None:
                del (request[k])
        return request[keyword]


Validate.register('set-choices', ValidateSetChoice)
Validate.register('validate-exclude', ValidateExclude)
