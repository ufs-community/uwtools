from collections.abc import Sequence


class TreeSearch:
    """
        Expects a dictionary with key build with dotted notation as a tree, e.g. a.b.d and does
        a 'reverse search', matches entries that are the most specific first.
        For example:
        d = {
            'a.b.c': value1,
            'b.c': value2,
            'c': value3
        }
        search:
          'a.b.c' -> value3
          'a.b': value1
          'c'-> value3

        search value can be passed either as:
          'a.b.c'
        or
          ['a', 'b', 'c']

        The separator can be customized.
        Please see test to help.
    """

    def __init__(self, data, separator='.'):
        self._data = data
        self._separator = separator

    def match(self, key):
        if isinstance(key, str):
            key = key.split(self._separator)
        elif not isinstance(key, Sequence):
            raise ValueError(f'Cannot manage the key: {key}')
        candidate = key[-1]
        keys = key[:-1]
        while candidate not in self._data and len(keys):
            candidate = keys[-1] + self._separator + candidate
            keys = keys[:-1]
        if candidate in self._data:
            return self._data[candidate]
        candidate = self._separator.join(key[:-1])
        keys = key[:-1]
        while candidate not in self._data and len(keys):
            candidate = self._separator.join(keys)
            keys = keys[:-1]
        return self._data.get(candidate, None)
