import re
from collections import defaultdict
from .basic import is_sequence_and_not_string, is_single_type_or_string


class Tag(dict):

    """
        find_tags looks recursively through lists and nested dictionaries for
        instances of "<tag>::<value>" statements that indicate a tag and an
        associated value. A tag is a string that could be used to qualify its value,
        for example indicate that the value is a file name that should be included:
            - include::
        or even the type of the file that should be included
            - yaml:: or json::

        Once all the tags have been found, we have a dictionary of tags,
        each tag being a list of locations in the main dictionary in the form of a
        string, for example a or a.b.c. The lists of locations are sorted so that
        the nearer to the root, the higher up in the list, for example:
        a, f.g, h.i and q.r.s would be sorted: [a, f.g, h.i, q.r.s]

        The extra arguments are tag names that you want filtered. No argument means return
        all tags, otherwise they are filtered.
    """

    def __init__(self, config, *args):
        super().__init__()
        tags = self.find_tags(config, *args)
        self.update(tags)

    @staticmethod
    def find_tags(config, *args):

        def my_sort(a):
            return len(a[0].split('.'))

        def split_tag(s: str):
            result = re.findall('^(.*?)::(.*)', s)
            # if there is a match, we receive a list of 1 tuple
            if len(result):
                result = result[0]
            if len(result) != 0 and len(result) != 2:
                raise ValueError(f'Cannot analyse tags in string {s}')
            if not len(result):
                return None, None
            return result

        def find_tags_inner(item, all_tags, path):
            if isinstance(item, dict):
                for k, i in item.items():
                    find_tags_inner(i, all_tags, path + [k])
            elif is_sequence_and_not_string(item):
                for i, v in enumerate(item):
                    find_tags_inner(v, all_tags, path + [f'[{i}]'])
            elif is_single_type_or_string(item):
                tag, value = split_tag(item)
                if tag is not None:
                    all_tags[tag].append(('.'.join(path), value))

        tags = defaultdict(list)
        find_tags_inner(config, tags, [])
        required = set(args)
        filtered = {}
        for kk, ii in tags.items():
            if not len(required) or kk in required:
                ii.sort(key=my_sort)
                filtered[kk] = ii
        return filtered
