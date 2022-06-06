# --------------------------------------------------------------------------------
# Author: JCSDA
#
# --------------------------------------------------------------------------------
import calendar
import re
import datetime


# ----------------------------------------------------------------------------
# Yet another Date class implementation. I kept my approach of "variable
# geometry" dates, e.g:
# - 2009             + 1  = 2010
# - 200902           + 1  = 200903
# - 20090201         + 1  = 20090202
# - 2009020112       + 12 = 2009020200
# - 200902011234     + 26 = 200902011300
# - 20090201123432   + 26 = 20090201123458
# ----------------------------------------------------------------------------

def to_components(value):
    if isinstance(value, str):
        value = re.sub('[^\\d]', '', value)

    _JULIAN_DATE_RE = re.compile(
        r'(?P<year>\d{4})(?P<doy>\d{3})(?P<hours>\d{2})?(?P<minutes>\d{2})?(?P<seconds>\d{2})?')

    components = []
    if type(value) == int:
        value = str(value)
    if len(value) % 2 == 1 and len(value) >= 7:
        # Julian date format; must be at least seven characters: YYYYDDD[HH[MM[SS]]]
        m = _JULIAN_DATE_RE.match(value)
        dt = datetime.datetime.strptime(f"{m.group('year')}{m.group('doy')}", '%Y%j')
        components.append(dt.year)
        components.append(dt.month)
        components.append(dt.day)
        if m.group('hours') is not None:
            components.append(int(m.group('hours')))
        if m.group('minutes') is not None:
            components.append(int(m.group('minutes')))
        if m.group('seconds') is not None:
            components.append(int(m.group('seconds')))

        length = len(components)
    else:
        value = int(value)
        while value > 10000:  # go to the year
            components.append(value % 100)
            value //= 100
        components.append(value)
        components.reverse()
        length = len(components)
        while len(components) < 3:
            components.append(1)

    return components, length


class DateIncrement(object):
    
    null_delta = datetime.timedelta()

    # Support for ISO 8601 for durations
    _TIMEDELTA_HOURS_RE = re.compile(
        r"^(?P<sign>[+-])?P?((?P<days>[\d\.]+)D)?(T?((?P<hours>[\d\.]+)[HZ])?((?P<minutes>[\d\.]+)M)?((?P<seconds>[\d\.]+)S)?)?$")
    _TIMEDELTA_TIME_RE = re.compile(
        r"^((?P<days>\d+)\s+day,\s+)?(?P<sign>[+-])?(?P<hours>\d{1,2})(:(?P<minutes>\d{1,2}))?(:(?P<seconds>\d{1,2}))?$")

    def parse_timedelta(self, date_string):
        '''
        parse timedelta format
        '''
        try:
            return datetime.timedelta(hours=float(date_string))
        except ValueError:
            pass
        m = self._TIMEDELTA_HOURS_RE.match(date_string)
        if not m:
            m = self._TIMEDELTA_TIME_RE.match(date_string)
        if m:
            days = 0 if m.group('days') is None else float(m.group('days'))
            hours = 0 if m.group('hours') is None else float(m.group('hours'))
            minutes = 0 if m.group('minutes') is None else float(m.group('minutes'))
            seconds = 0 if m.group('seconds') is None else float(m.group('seconds'))
            dt = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            if m.group('sign') is not None and m.group('sign') == '-':
                dt = -dt
            return dt
        else:
            raise ValueError("Unable to parse '%s' as a timedelta" % date_string)

    def __init__(
                self,
                duration=None,
                years=0,
                months=0,
                days=0,
                hours=0,
                minutes=0,
                seconds=0):
        self.years = years
        self.months = months
        if duration is not None:
            if type(duration) == datetime.timedelta:
                self.delta = duration
            elif type(duration) == self.__class__:
                self.delta = duration.delta
            else:
                self.delta = self.parse_timedelta(duration)
        else:
            self.delta = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    def add(self, date):
        if self.delta != self.null_delta:
            date += self.delta
        if self.months != 0:
            value = abs(self.months)
            months = value % 12
            years = value // 12
            if self.months < 0:
                months = -months
                years = -years
            months = date.month + months
            years = date.year + years
            while (months < 1) or (months > 12):
                if months < 1:
                    months += 12
                    years -= 1
                elif months > 12:
                    months -= 12
                    years += 1
            date = date.replace(year=years)
            date = date.replace(month=months)
        if self.years != 0:
            date = date.replace(year=date.year+self.years)
        return date

    def __add__(self, what):
        if type(what) != DateIncrement:
            raise NotImplementedError('Operator + between DateIncrement')
        new = DateIncrement()
        new.delta = self.delta + what.delta
        return new
        
    def __neg__(self):
        new = DateIncrement()
        new.delta = -self.delta
        new.months = -self.months
        new.years = -self.years
        return new

    def __eq__(self, value):
        if isinstance(value, DateIncrement):
            return self.months == value.months and self.years == value.years and self.delta == value.delta
        return self.months == value and self.years == value and self.delta.days == 0 and self.delta.seconds == 0

    def __repr__(self):
        return str(self)

    def __str__(self):
        # Prints out in ISO 8601 for durations
        td = 'P'
        if self.delta.days > 0:
            td += str(self.delta.days) + 'D'
        td += 'T'
        hh, r = divmod(self.delta.seconds, 3600)
        mm, ss = divmod(r, 60)
        if hh > 0:
            td += str(hh) + 'H'
        if mm > 0:
            td += str(mm) + 'M'
        if ss > 0:
            td += str(ss) + 'S'
        if td[-1] == 'T':
            td = td[:-1]
        return td

    def __hash__(self):
        return int(self.delta.total_seconds())

    def __getattr__(self, attribute):
        if hasattr(self.delta, attribute):
            return getattr(self.delta, attribute)
        raise AttributeError(attribute)

    def total_seconds(self):
        return int(self.delta.total_seconds())


# ----------------------------------------------------------------------------
# Generic public Date entry
# ----------------------------------------------------------------------------
class Date(object):

    def __new__(cls, value=None):
        if value is None:
            value = datetime.datetime.now()
        if isinstance(value, CoreDate):
            return value.__class__(value.date)
        elif isinstance(value, datetime.datetime):
            return Second(value)
        elif isinstance(value, datetime.date):
            value = datetime.datetime(value.year, value.month, value.day)
            return Second(value)
        components, length = to_components(value)
        return switch[length](datetime.datetime(*components))


# ----------------------------------------------------------------------------
# Generic private Date entry
# ----------------------------------------------------------------------------
class CoreDate(object):
    
    no_separators = re.compile('[:\\-\\s]')

    def __init__(self, date):
        if isinstance(date, CoreDate):
            self.date = date.date
        elif isinstance(date, datetime.datetime):
            self.date = date
        elif isinstance(date, datetime.date):
            self.date = datetime.datetime(date.year, date.month, date.day)
        else:
            components, _ = to_components(date)
            self.date = datetime.datetime(*components)

    # -------------------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------------------
    def datetime(self):
        return self.date

    def year(self):
        return "%04d" % self.date.year

    def month(self):
        return "%02d" % self.date.month

    def day(self):
        return "%02d" % self.date.day

    def hour(self):
        return "%02d" % self.date.hour

    def year_int(self):
        return self.date.year

    def month_int(self):
        return self.date.month

    def day_int(self):
        return self.date.day

    def hour_int(self):
        return self.date.hour

    def minute_int(self):
        return self.date.minute

    def second_int(self):
        return self.date.second

    def int_value(self):
        return int(re.sub(CoreDate.no_separators, '', self.__str__()))

    def string_value(self):
        return re.sub(CoreDate.no_separators, '', self.__str__())

    def __str__(self):
        return self.date.strftime(self.template())
    __repr__ = __str__

    def unix_timestamp(self):
        return calendar.timegm(self.datetime().utctimetuple())

    def format(self, fmt=None):
        if not fmt:
            fmt = self.template()
        return self.date.strftime(fmt)

    def iso_8601(self, timezone=None):
        s = self.date.strftime("%Y-%m-%dT%H:%M:%S")
        if timezone is not None:
            s += timezone
        return s

    def is_round_multiple(self, number_in_seconds):
        t = int(self.unix_timestamp())
        return (t % number_in_seconds) == 0

    def last_round_multiple(self, increment_in_seconds):
        t = int(self.unix_timestamp())
        d = t // increment_in_seconds
        return date_from_timestamp(increment_in_seconds * d)

    def next_round_multiple(self, increment_in_seconds):
        return self.last_round_multiple(increment_in_seconds) + increment_in_seconds

    def iso_date(self):
        return self.date.strftime('%a, %d %b %Y %H:%M:%S') + ' +0000'

    # -------------------------------------------------------------------------
    # Arithmetic and comparisons
    # -------------------------------------------------------------------------
    def __add__(self, what):
        new = Date(self)
        new += what
        return new
    __radd__ = __add__

    def __iadd__(self, what):
        if not isinstance(what, (int, float, DateIncrement)):
            raise ValueError("only a number or a DateIncrement can be added to a date")
        if not isinstance(what, DateIncrement):
            what = DateIncrement(**self.unit(what))
        self.date = what.add(self.date)
        return self

    def __sub__(self, what):
        if not isinstance(what, CoreDate):
            new = Date(self)
            new -= what
            return new
        else:
            if self.date > what.date:
                new = self.subtract(self.date, what.date)
            else:
                new = - self.subtract(what.date, self.date)
        return new

    def __rsub__(self, other):
        raise SystemError('Right-hand side subtract is not implemented')

    def __isub__(self, what):
        if not isinstance(what, (int, float, DateIncrement)):
            raise ValueError("only a number or a DateIncrement can be added to a date")
        if not isinstance(what, DateIncrement):
            what = DateIncrement(**self.unit(-what))
        else:
            what = -what
        self.date = what.add(self.date)
        return self

    def __eq__(self, other):
        if not isinstance(other, CoreDate):
            other = Date(other)
        return self.date == other.date

    def __ne__(self, other):
        if not isinstance(other, CoreDate):
            other = Date(other)
        return self.date != other.date

    def __gt__(self, other):
        if not isinstance(other, CoreDate):
            other = Date(other)
        return self.date > other.date

    def __ge__(self, other):
        if not isinstance(other, CoreDate):
            other = Date(other)
        return self.date >= other.date

    def __lt__(self, other):
        if not isinstance(other, CoreDate):
            other = Date(other)
        return self.date < other.date

    def __le__(self, other):
        if not isinstance(other, CoreDate):
            other = Date(other)
        return self.date <= other.date

    def __hash__(self):
        return self.int_value()

    # for the sake of PyCharm
    @staticmethod
    def template():
        return ''

    @staticmethod
    def unit(what):
        return {}

    @staticmethod
    def subtract(a, b):
        return a-b


# ----------------------------------------------------------------------------
# Date yyyymmddhhMMss
# ----------------------------------------------------------------------------
class Second(CoreDate):

    @staticmethod
    def template():
        return "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def unit(value):
        return {'seconds': value}

    @staticmethod
    def subtract(a, b):
        c = a-b
        return c.days * 86400 + c.seconds


# ----------------------------------------------------------------------------
# Date yyyymmddhhMM
# ----------------------------------------------------------------------------
class Minute(CoreDate):
    
    @staticmethod
    def template():
        return "%Y-%m-%d %H:%M"

    @staticmethod
    def unit(value):
        return {'minutes': value}

    @staticmethod
    def subtract(a, b):
        b = b.replace(second=0)
        c = a-b
        return c.days * 1440 + c.seconds // 60


# ----------------------------------------------------------------------------
# Date yyyymmddhh
# ----------------------------------------------------------------------------
class Hour(CoreDate):

    @staticmethod
    def template():
        return "%Y-%m-%d %H"

    @staticmethod
    def unit(value):
        return {'hours': value}

    @staticmethod
    def subtract(a, b):
        b = b.replace(second=0, minute=0)
        c = a-b
        return c.days * 24 + c.seconds // 3600


# ----------------------------------------------------------------------------
# Date yyyymmdd
# ----------------------------------------------------------------------------
class Day(CoreDate):

    @staticmethod
    def template():
        return "%Y-%m-%d"

    @staticmethod
    def unit(value):
        return {'days': value}

    @staticmethod
    def subtract(a, b):
        b = b.replace(second=0, minute=0, hour=0)
        c = a-b
        return c.days


# ----------------------------------------------------------------------------
# Date yyyymm
# ----------------------------------------------------------------------------
class Month(CoreDate):

    @staticmethod
    def template():
        return "%Y-%m"

    @staticmethod
    def unit(value):
        return {'months': value}

    @staticmethod
    def subtract(a, b):
        return a.month - b.month + (a.year - b.year) * 12


# ----------------------------------------------------------------------------
# Date yyyy
# ----------------------------------------------------------------------------
class Year(CoreDate):

    @staticmethod
    def template():
        return "%Y"

    @staticmethod
    def unit(value):
        return {'years': value}

    @staticmethod
    def subtract(a, b):
        return a.year - b.year


class JediDate(Second):
    @staticmethod
    def template():
        return "%Y-%m-%dT%H:%M:%SZ"


switch = {
    1: Year,
    2: Month,
    3: Day,
    4: Hour,
    5: Minute,
    6: Second,
}


# ----------------------------------------------------------------------------
# arguments are taken 3 at a time
# dates = date_sequence(d11,d12,inc1,d21,d22,inc2,...,dn1,dn2,inc_n,format = '%Y%m%d')
# returns the concatenation of sequences of dates.§
# ----------------------------------------------------------------------------
def date_sequence(*args, **kwargs):
    args = list(args)
    if len(args) == 2:
        # defaults to increment by 1 unit
        args.append(1)
    elif len(args) % 3 != 0:
        raise ValueError('Arguments should work in triples: date1, date2, increment,...')
    fmt = None
    if 'format' in kwargs:
        fmt = kwargs['format']
    i = 0
    while i < len(args):
        begin = Date(args[i])
        end = Date(args[i+1])
        increment = args[i+2]
        if isinstance(increment, str):
            try:
                i = int(increment)
            except ValueError:
                # it's probably an iso duration
                increment = DateIncrement(increment)
        i += 3
        if increment == 0:
            raise ValueError('An increment of 0 does not make much sense')
        if begin <= end:
            while begin <= end:
                if fmt:
                    yield begin.format(fmt)
                else:
                    yield begin.int_value()
                begin += increment
        else:
            while begin >= end:
                if fmt:
                    yield begin.format(fmt)
                else:
                    yield int(begin.int_value())
                begin += increment


def step_sequence(start_step, end_step, increment):
    start_step = DateIncrement(start_step)
    end_step = DateIncrement(end_step)
    increment = DateIncrement(increment)
    sequence = []
    step = start_step
    while step.total_seconds() <= end_step.total_seconds():
        sequence.append(str(step))
        step += increment
    return sequence


def date_from_timestamp(value):
    return Date(datetime.datetime.utcfromtimestamp(float(value)))


def utc_now():
    return Date(datetime.datetime.utcnow())


def iso_date_to_date(date):
    all_dates = date.split(' ')
    date = ' '.join(all_dates[:-1])
    offset = all_dates[-1]
    d = Date(datetime.datetime.strftime(datetime.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S'), '%Y%m%d%H%M%S'))
    sign = offset[0]
    value = DateIncrement(hours=int(offset[1:])//100)
    if sign == '+':
        d -= value
    elif sign == '-':
        d += value
    else:
        raise ValueError('Cannot decode %s' % date)
    return d


def mysql_date_to_date(date):
    date = re.sub('[ :-]', '', date)
    return Date(date)
