from solo.date import Date, Day, Month, Year, Hour, Minute, Second, DateIncrement

reference = dict(day=27,
                 month=4,
                 year=2017,
                 hour=17,
                 minute=50,
                 second=5
                 )
day_plus_5 = '2017-05-02'
month_plus_5 = '2017-09'
year_plus_5 = '2022'
hour_plus_5 = '2017-04-27 22'
minute_plus_5 = '2017-04-27 17:55'
second_plus_5 = '2017-04-27 17:50:10'
day_minus_5 = '2017-04-22'
month_minus_5 = '2016-11'
year_minus_5 = '2012'
hour_minus_5 = '2017-04-27 12'
minute_minus_5 = '2017-04-27 17:45'
second_minus_5 = '2017-04-27 17:50:00'

julian_dates = ['2017117175005', '2017117', '201711717', '20171171750']
julian_dates_refs = ['2017-04-27 17:50:05', '2017-04-27', '2017-04-27 17', '2017-04-27 17:50']


def build_date():
    return '%d-%02d-%02d %02d:%02d:%02d' % (
        reference['year'],
        reference['month'],
        reference['day'],
        reference['hour'],
        reference['minute'],
        reference['second'])

def compare_dates(d, *fields):
    comparisons = []
    for field in fields:
        comparisons.append((reference.get(field), getattr(d, '%s_int' % field)))
    for me, them in comparisons:
        assert me == them()


# ------------------------------------------------------------
# Date creation
# ------------------------------------------------------------
def test_create_system_date():
    try:
        Date()
    except Exception as e:
        raise AssertionError('System date creation failed %s' % e)


def test_create_date_int():
    try:
        Date(20170427)
    except Exception as e:
        raise AssertionError('Int date creation failed %s' % e)


def test_create_date_str():
    try:
        Date('20170427')
    except Exception as e:
        raise AssertionError('Str date creation failed %s' % e)


def test_create_date_str_formatted():
    try:
        Date('2017-04-27')
    except Exception as e:
        raise AssertionError('Str formatted date creation failed %s' % e)


def test_create_jedi_date():
    try:
        Date('2017-04-27T00:00:00Z')
    except Exception as e:
        raise AssertionError('Str formatted date creation failed %s' % e)


def test_create_date_from_date():
    date = Date('2017-04-27')
    try:
        Date(date)
    except Exception as e:
        raise AssertionError('date creation from date failed %s' % e)


def test_create_date_from_datetime():
    date = Date('2017-04-27')
    try:
        Date(date.datetime())
    except Exception as e:
        raise AssertionError('date creation from datetime failed %s' % e)


# ------------------------------------------------------------
# Day creation
# ------------------------------------------------------------
def test_create_day_from_date():
    date = build_date()
    try:
        d = Day(date)
    except Exception as e:
        raise AssertionError('day creation from date failed %s' % e)
    compare_dates(d, 'year', 'month', 'day')


# ------------------------------------------------------------
# Month creation
# ------------------------------------------------------------
def test_create_month_from_date():
    date = Date('2017-04-27')
    try:
        d = Month(date)
    except Exception as e:
        raise AssertionError('month creation from date failed %s' % e)
    compare_dates(d, 'year', 'month')


# ------------------------------------------------------------
# Year creation
# ------------------------------------------------------------
def test_create__year_from_date():
    date = Date('2017-04-27')
    try:
        d = Month(date)
    except Exception as e:
        raise AssertionError('year creation from date failed %s' % e)
    compare_dates(d, 'year')


# ------------------------------------------------------------
# Hour creation
# ------------------------------------------------------------
def test_create_hour_from_date():
    date = build_date()
    try:
        d = Hour(date)
    except Exception as e:
        raise AssertionError('hour creation from date failed %s' % e)
    compare_dates(d, 'year', 'month', 'day', 'hour')


# ------------------------------------------------------------
# Minute creation
# ------------------------------------------------------------
def test_create_minute_from_date():
    date = build_date()
    try:
        d = Minute(date)
    except Exception as e:
        raise AssertionError('minute creation from date failed %s' % e)
    compare_dates(d, 'year', 'month', 'day', 'hour', 'minute')


# ------------------------------------------------------------
# Second creation
# ------------------------------------------------------------
def test_create_second_from_date():
    date = build_date()
    try:
        d = Second(date)
    except Exception as e:
        raise AssertionError('second creation from date failed %s' % e)
    compare_dates(d, 'year', 'month', 'day', 'hour', 'minute', 'second')


# ------------------------------------------------------------
# Addition, subtraction
# ------------------------------------------------------------
def test_add_day():
    date = Day(build_date())
    new_date = date + 5
    assert str(new_date) == day_plus_5
    d = Day(date)
    d += 5
    assert str(d) == day_plus_5


def test_add_month():
    date = Month(build_date())
    new_date = date + 5
    assert str(new_date) == month_plus_5
    d = Month(date)
    d += 5
    assert str(d) == month_plus_5


def test_add_year():
    date = Year(build_date())
    new_date = date + 5
    assert str(new_date) == year_plus_5
    d = Year(date)
    d += 5
    assert str(d) == year_plus_5


def test_add_hour():
    date = Hour(build_date())
    new_date = date + 5
    assert str(new_date) == hour_plus_5
    d = Hour(date)
    d += 5
    assert str(d) == hour_plus_5


def test_add_minute():
    date = Minute(build_date())
    new_date = date + 5
    assert str(new_date) == minute_plus_5
    d = Minute(date)
    d += 5
    assert str(d) == minute_plus_5


def test_add_second():
    date = Second(build_date())
    new_date = date + 5
    assert str(new_date) == second_plus_5
    d = Second(date)
    d += 5
    assert str(d) == second_plus_5


def test_subtract_day():
    date = Day(build_date())
    new_date = date - 5
    assert str(new_date) == day_minus_5
    d = Day(date)
    d -= 5
    assert str(d) == day_minus_5


def test_subtract_month():
    date = Month(build_date())
    new_date = date - 5
    assert str(new_date) == month_minus_5
    d = Month(date)
    d -= 5
    assert str(d) == month_minus_5


def test_subtract_year():
    date = Year(build_date())
    new_date = date - 5
    assert str(new_date) == year_minus_5
    d = Year(date)
    d -= 5
    assert str(d) == year_minus_5


def test_subtract_hour():
    date = Hour(build_date())
    new_date = date - 5
    assert str(new_date) == hour_minus_5
    d = Hour(date)
    d -= 5
    assert str(d) == hour_minus_5


def test_subtract_minute():
    date = Minute(build_date())
    new_date = date - 5
    assert str(new_date) == minute_minus_5
    d = Minute(date)
    d -= 5
    assert str(d) == minute_minus_5


def test_subtract_second():
    date = Second(build_date())
    new_date = date - 5
    assert str(new_date) == second_minus_5
    d = Second(date)
    d -= 5


# ------------------------------------------------------------
# Some special cases
# ------------------------------------------------------------
def test_leap_year():
    d = Day(Date('2012-02-28'))
    new_date = d + 5
    assert str(new_date) == '2012-03-04'
    d = Day(Date('2012-03-03'))
    new_date = d - 63
    assert str(new_date) == '2011-12-31'


def test_non_leap_year():
    d = Day(Date('2013-02-28'))
    new_date = d + 5
    assert str(new_date) == '2013-03-05'
    d = Day(Date('2013-03-03'))
    new_date = d - 63
    assert str(new_date) == '2012-12-30'


def test_change_of_year():
    d = Month('2014-11')
    d += 2
    assert d.year_int() == 2015


def test_one_second_to_new_year():
    d = Date('2017-12-31 23:59:59')
    d += 1
    assert str(d) == '2018-01-01 00:00:00'


def test_date_increment():
    date = Date(build_date())
    increment = DateIncrement(years=1, months=1, days=1, hours=1, minutes=1, seconds=1)
    date += increment
    assert str(date) == '2018-05-28 18:51:06'


def test_iso_duration():
    increment = DateIncrement(days=2, hours=12, minutes=30, seconds=7)
    assert str(increment) == 'P2DT12H30M7S'


def test_increment_addition():
    increment = DateIncrement('PT3H')
    increment += increment
    assert str(increment) == 'PT6H'


def no_t_at_the_end():
    # testing a case where we make sure that DateIncrement's conversion
    # to iso duration doesn't not produce 'P1DT' like it used to
    increment = DateIncrement('PT33H')
    assert str(increment) == 'P1D'


def test_julian():
    for jdate, jdate_ref in zip(julian_dates, julian_dates_refs):
        try:
            julian_date = Date(jdate)
        except Exception as e:
            raise AssertionError('Failed to convert julian date' % e)
        assert julian_date == jdate_ref
