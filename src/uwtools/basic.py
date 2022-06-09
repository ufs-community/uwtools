# --------------------------------------------------------------------------------
# Author: JCSDA
#
# --------------------------------------------------------------------------------
import re
import copy
import uuid
from collections.abc import Sequence
import itertools
from random import randint

"""
    Some pretty basic functions not to be undermined, they enable the programmer to write cleaner code.
"""


def is_list(a):
    return type(a) == list or type(a) == tuple


def to_list(a):
    if not is_list(a):
        a = [a]
    return a


def no_list(a):
    if is_list(a):
        a = a[0]
    return a


def simplify_list(a):
    if is_list(a):
        if len(a) == 1:
            a = a[0]
    return a



def chunk_iter(chunk_size, iterable, pad=False, padvalue=None):
    """
    Return a generator for chunks of chunk_size from the iterable.  The last chunk may be filled with padvalue
    """
    if pad:
        return itertools.zip_longest(*[iter(iterable)]*chunk_size, fillvalue=padvalue)
    else:
        # Filter out values of 'None'
        return ([x for x in chunk if x is not None] for chunk in chunk_iter(chunk_size, iterable, pad=True))


def is_sequence_and_not_string(a):
    return isinstance(a, Sequence) and not isinstance(a, str)


def is_single_type(s):
    try:
        len(s)
    except TypeError:
        return True
    else:
        return False


def is_single_type_or_string(s):
    if isinstance(s, str):
        return True
    try:
        len(s)
    except TypeError:
        return True
    else:
        return False


def unique_id():
    return uuid.uuid4().hex


def random_from_string(digit_count: int, pattern: str):
    """
        Generate a string of length digit_count with values picked
        randomly from the pattern
    """
    result = ''
    for x in range(digit_count):
        y = randint(0, len(pattern) - 1)
        result += pattern[y]
    return result


def increment_string(identifier: str, pattern: str):
    """
        Increments the identifier using the pattern as a "base"
    """
    d = identifier[-1]
    index = pattern.find(d)
    if index == -1:
        raise ValueError(f'{identifier} contains a character that is not in the pattern {pattern}')
    # carry over
    if index == len(pattern) - 1:
        if len(identifier) > 1:
            identifier = increment_string(identifier[:-1], pattern) + pattern[0]
        else:
            raise ValueError(f'{identifier} is out of capacity.')
    else:
        identifier = identifier[:-1] + pattern[index + 1]
    return identifier


def convert_to_base(value: str, base: str, width=0):
    """
        converts a integer base 10 value sent as a string into the base as describe in the base parameter
        base is a string containing all characters present in the base, lower values first.
        width is the number of charaters the returned value should have, it is padded to the left with zeros
    """
    modulo = len(base)
    value = int(value)
    converted = ''
    while value >= modulo:
        mod = value % modulo
        converted = base[mod] + converted
        value = value // modulo
    converted = base[value] + converted
    converted = '0' * (width - len(converted)) + converted
    return converted


def time_in_seconds(s):
    """
    :param s: a string, for example 12, 12mn, 4h, 4hours, 2 days etc...
    :return: the time in seconds
    """
    factors = {
        's': 1,
        'second': 1,
        'seconds': 1,
        'mn': 60,
        'm': 60,
        'minute': 60,
        'minutes': 60,
        'h': 3600,
        'hour': 3600,
        'hours': 3600,
        'd': 86400,
        'day': 86400,
        'days': 86400,
    }

    s = str(s).lower().strip()
    negative = False
    if s[0] == '-':
        negative = True
        s = s[1:]
    units = re.findall('[a-z]+', s)
    numbers = re.findall('[0-9]+', s)
    duration = 0
    factor = 1
    if len(units) != len(numbers):
        raise ValueError('In time %s, cannot decode the format' % s)
    for u, n in zip(units, numbers):
        if u not in factors:
            raise ValueError('In time %s, unknown unit: %s' % (s, u))
        factor = factors[u]
        if negative:
            factor = -factor
        duration += int(n) * factor
    return duration


def big_number(value):
    """
        Formats a number to add comas for multiples of 1,000
    """
    s = str(value)
    parts = s.split('.')
    whole = parts[0]
    dec = ''
    if len(parts) > 1:
        dec = parts[1]
    new = ''
    ll = len(whole)
    for i in range(ll):
        index = ll - i - 1
        new += whole[i]
        if index % 3 == 0 and index != 0:
            new += ','
    if len(dec) > 0:
        new += '.' + dec
    return new


def big_number_short(value):
    """
        Shortens a number to the nearest factor (K, M, B)
    """
    abbreviations = ['', 'K', 'M', 'B']

    value = float(value)
    i = 0
    while value >= 1000 and i < len(abbreviations):
        i += 1
        value /= 1000
    v = str(value)
    v = v.replace('.0', '')
    return v + abbreviations[i]


def camel_case_to_snake_case(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


def split_camel_case(s: str):
    groups = re.findall(r'[A-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', s)
    if not len(groups):
        groups = [s]
    return groups


def combine(variables: list, dictionary: dict, visitor, *args, **kwargs):
    """
        Generates all combinations of variables named in variables
        for all values in dictionary, for example:
            variables = ['model', 'colour']
            dictionary = { 'model': ['a3', 'a4', 'a5'], 'colour': ['red', 'blue'] }
            def visitor(result, *args, **kwargs):
                print(result)
            visitor is called with:
               { 'model': 'a3', 'colour': 'red' }
               { 'model': 'a3', 'colour': 'blue' }
               { 'model': 'a4', 'colour': 'red' }
               { 'model': 'a4', 'colour': 'blue' }
               { 'model': 'a5', 'colour': 'red' }
               { 'model': 'a5', 'colour': 'blue' }
    """
    def _combine(variables: list, dictionary: dict, result: dict):
        result = copy.copy(result)
        for value in dictionary[variables[0]]:
            result[variables[0]] = value
            if len(variables) > 1:
                _combine(variables[1:], dictionary, result)
            else:
                visitor(copy.copy(result), *args, **kwargs)
    _combine(variables, dictionary, dictionary)


def traverse_structure(structure, visitor, *args, **kwargs):
    """
    The visitor receives a basic item (not list or dictionary)
    and returns it potentially transformed.
    The structure is duplicated into plain dicts in the process
    """
    new = structure
    if isinstance(structure, dict):
        new = {}
        for key, item in structure.items():
            new[key] = traverse_structure(item, visitor)
    elif isinstance(structure, list):
        new = []
        for item in structure:
            new.append(traverse_structure(item, visitor))
    else:
        new = visitor(structure, *args, **kwargs)
    return new
