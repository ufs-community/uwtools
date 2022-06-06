import os
import pytest
from solo.basic import time_in_seconds, \
    big_number, \
    big_number_short,\
    camel_case_to_snake_case, \
    combine, \
    increment_string, \
    convert_to_base

# ------------------------------------------------------------
# time_in_seconds. Split into different methods to help
# locate the error quickly.
# ------------------------------------------------------------
duration = [
    ('10s', 10),
    ('10 s', 10),
    ('55second', 55),
    ('55 second', 55),
    ('123seconds', 123),
    ('123 seconds', 123),
    ('3mn', 180),
    ('3 mn', 180),
    ('5m', 300),
    ('5 m', 300),
    ('35minute', 2100),
    ('35 minute', 2100),
    ('45minutes', 2700),
    ('45 minutes', 2700),
    ('2h', 7200),
    ('2 h', 7200),
    ('5hour', 18000),
    ('5 hour', 18000),
    ('12hours', 43200),
    ('12 hours', 43200),
    ('1d', 86400),
    ('1 d', 86400),
    ('3day', 259200),
    ('3 day', 259200),
    ('31days', 2678400),
    ('31 days', 2678400),
    ('2 days 3 hours', 183600),
    ('2d3h', 183600),
    ('2d3h12mn45s', 184365),
    ('2 days 3 hours 12 MINUTES 45 seconds', 184365)
]

base = '0123456789abcdefghijklmnopqrstuvwxyz'


def evaluate(index):
    assert duration[index][1] == time_in_seconds(duration[index][0])


def test_time_in_seconds00():
    evaluate(0)


def test_time_in_seconds01():
    evaluate(1)


def test_time_in_seconds02():
    evaluate(2)


def test_time_in_seconds03():
    evaluate(3)


def test_time_in_seconds04():
    evaluate(4)


def test_time_in_seconds05():
    evaluate(5)


def test_time_in_seconds06():
    evaluate(6)


def test_time_in_seconds07():
    evaluate(7)


def test_time_in_seconds08():
    evaluate(8)


def test_time_in_seconds09():
    evaluate(9)


def test_time_in_seconds10():
    evaluate(10)


def test_time_in_seconds11():
    evaluate(11)


def test_time_in_seconds12():
    evaluate(12)


def test_time_in_seconds13():
    evaluate(13)


def test_time_in_seconds14():
    evaluate(14)


def test_time_in_seconds15():
    evaluate(15)


def test_time_in_seconds16():
    evaluate(16)


def test_time_in_seconds17():
    evaluate(17)


def test_time_in_seconds18():
    evaluate(18)


def test_time_in_seconds19():
    evaluate(19)


def test_time_in_seconds20():
    evaluate(20)


def test_time_in_seconds21():
    evaluate(21)


def test_time_in_seconds22():
    evaluate(22)


def test_time_in_seconds23():
    evaluate(23)


def test_time_in_seconds24():
    evaluate(24)


def test_time_in_seconds25():
    evaluate(25)


def test_time_in_seconds26():
    evaluate(26)


def test_time_in_seconds27():
    evaluate(27)


def test_time_in_seconds28():
    evaluate(28)


def test_time_in_seconds29():
    evaluate(29)


# ------------------------------------------------------------
# Big Number
# ------------------------------------------------------------
def test_big_number_thousand():
    assert big_number(3000) == '3,000'


def test_big_number_thousand_float():
    assert big_number(3000.12) == '3,000.12'


def test_big_number_million():
    assert big_number(1756342) == '1,756,342'


def test_big_number_million_float():
    assert big_number(1756342.25) == '1,756,342.25'


def test_big_number_billion():
    assert big_number(1756342498) == '1,756,342,498'


def test_big_number_billion_float():
    assert big_number(1756342498.999) == '1,756,342,498.999'


# ------------------------------------------------------------
# Big Number Short
# ------------------------------------------------------------
def test_big_number_short_thousand():
    assert big_number_short(3000) == '3K'


def test_big_number_short_thousand_half():
    assert big_number_short(3500) == '3.5K'


def test_big_number_short_thousand_decimal():
    assert big_number_short(3542) == '3.542K'


def test_big_number_short_million():
    assert big_number_short(2000000) == '2M'


def test_big_number_short_million_half():
    assert big_number_short(2500000) == '2.5M'


def test_big_number_short_million_decimal():
    assert big_number_short(2546712) == '2.546712M'


def test_big_number_short_billion():
    assert big_number_short(2000000000) == '2B'


def test_big_number_short_billion_half():
    assert big_number_short(2500000000) == '2.5B'


def test_big_number_short_billion_decimal():
    assert big_number_short(2500436000) == '2.500436B'


def test_camel_case_to_snake_case():
    camel = 'TestCamelCase'
    snake = 'test_camel_case'
    assert camel_case_to_snake_case(camel) == snake


def test_combine():
    def visitor(r, result):
        print(r)
        result.append(r)

    variables = ['model', 'colour']
    dictionary = dict(
        model=['a3', 'a4', 'a5'],
        colour=['red', 'blue'],
        extra_field=True
    )
    expected_result = [
        {'model': 'a3', 'colour': 'red', 'extra_field': True},
        {'model': 'a3', 'colour': 'blue', 'extra_field': True},
        {'model': 'a4', 'colour': 'red', 'extra_field': True},
        {'model': 'a4', 'colour': 'blue', 'extra_field': True},
        {'model': 'a5', 'colour': 'red', 'extra_field': True},
        {'model': 'a5', 'colour': 'blue', 'extra_field': True},
    ]
    result = []
    combine(variables, dictionary, visitor, result)
    assert result == expected_result
    for d in result:
        assert 'extra_field' in d and d['extra_field']

def test_increment_string():
    assert increment_string('a000', base) == 'a001'
    assert increment_string('a00z', base) == 'a010'
    assert increment_string('a0zz', base) == 'a100'
    assert increment_string('zzzy', base) == 'zzzz'
    with pytest.raises(ValueError):
        # tests out of capacity
        increment_string('zzzz', base)

def test_convert_to_base():
    assert convert_to_base('0', base, 4) == '0000'
    assert convert_to_base('36', base, 4) == '0010'
    assert convert_to_base('23806', base, 4) == '0ida'
    assert convert_to_base('123806', base, 4) == '2nj2'

