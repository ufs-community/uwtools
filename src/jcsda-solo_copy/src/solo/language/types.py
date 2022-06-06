# --------------------------------------------------------------------------------
# Author: JCSDA
#
# --------------------------------------------------------------------------------
import re
import builtins
from ..factory import create_factory
from ..date import Day, DateIncrement, JediDate
from ..basic import big_number, time_in_seconds
from ..template import TemplateConstants, Template


factory = create_factory('TypeCreation')


class Types(factory):

    mapping = {
        'string': 'str'
    }

    @classmethod
    def create(cls, name, *args, **kwargs):
        try:
            result = super(Types, cls).create(name, *args, **kwargs)
        except IndexError:
            if name in cls.mapping:
                name = cls.mapping[name]
            result = getattr(builtins, name)(*args, **kwargs)
        return result


class BigNumber(int):
    def __new__(cls, value):
        if isinstance(value, str):
            value = int(re.sub(',', '', value))
        return int.__new__(value)

    def __str__(self):
        s = super(BigNumber, self).__str__()
        return big_number(s)


class PyDate(object):
    def __new__(cls, value):
        # will issue an exception if the date is not valid
        return Day(value)


class PyJediDate(object):
    def __new__(cls, value):
        # will issue an exception if the date is not valid
        return JediDate(value)


class Boolean(object):
    def __new__(cls, value):
        result = False
        if isinstance(value, str):
            value = value.lower()
            if value == 'yes' or value == 'y':
                result = True
        elif isinstance(value, bool):
            result = value
        elif isinstance(value, int):
            result = value != 0
        return result


class Path(object):
    def __new__(cls, value):
        value = Template.substitute_structure_from_environment(value)
        return value


class Duration(object):
    def __new__(cls, value):
        seconds = time_in_seconds(value)
        return seconds


class ISODuration(object):
    def __new__(cls, value):
        increment = DateIncrement(value)
        return increment


class FormattedDuration(object):
    def __new__(cls, value):
        return str(DateIncrement(value))


Types.register('big_number', BigNumber)
Types.register('date', PyDate)
Types.register('jedi_date', PyJediDate)
Types.register('boolean', Boolean)
Types.register('path', Path)
Types.register('duration', Duration)
Types.register('iso_duration', ISODuration)
Types.register('formatted_duration', FormattedDuration)
