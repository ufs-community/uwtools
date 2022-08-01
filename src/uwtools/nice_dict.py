'''
NiceDict is overloaded Python dictionary used for pretty printing
and in support of YAML inline strigification
'''
# (C) Copyright 2020-2022 UCAR
#
# This software is licensed under the terms of the Apache License Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# Part of this software is developed by the Joint Center for
# Satellite Data Assimilation (JCSDA) together with its partners.

import re
import yaml

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

class NiceDict(dict):

    """
        A dictionary with a nice hierarchical print capability
        dictionary elements can be accessed as if they are members:
        d = NiceDict(
            a=1,
            b=2
        )
        d.a + d.b (3)
    """

    def __clean_str__(self, data, level):
        contents = []
        tab = ' ' * (level * 2)
        keys = sorted(data.keys())
        for k in keys:
            key = str(k)
            key = tab + key + ':' + ' ' * (8 - len(k)) + ' '
            # don't display keywords starting with _ (private)
            if k[0] != '_':
                i = data[k]
                if isinstance(i, dict):
                    key += '\n'
                    value = self.__clean_str__(i, level+1)
                elif isinstance(i, list):
                    key += '\n'
                    rows = []
                    #pylint: disable=invalid-name
                    for x in i:
                        if isinstance(x, dict):
                            rows.append(self.__clean_str__(x, level+1))
                        else:
                            rows.append(' ' * (len(key)-len(tab)) + str(x))
                    value = '\n'.join(rows)
                else:
                    value = str(i)
                contents.append(f'{key}{value}')
        return '\n'.join(contents)

    def __str__(self):
        return self.__clean_str__(self, 1)

    def __getattr__(self, item):
        if item in self:
            return self[item]
        raise AttributeError(f"'{type(self)}' object has no attribute '{item}'")

    def flatten(self):
        """
            Flattens the hierarchical dictionaries to have all fields
            available root level.
            Let's hope that our lovely developers do not use the same
            keywords at different levels of the hierarchy or this feature is useless :)
            Does not alter the original objects.
        """
        result = {}
        return self._flatten(self, result)

    def _flatten(self, obj, result):
        for key, item in obj.items():
            if isinstance(item, dict):
                self._flatten(item, result)
            else:
                result[key] = item
        return result

    def save_yaml(self, path):
        '''Save pretty printing yaml file from withing NiceDict Class'''
        def do_nothing(item):
            return item

        # duplicate the structure to plain objects
        # so that yaml doesn't bug us with references
        copy = traverse_structure(self, do_nothing)
        with open(path, 'w', encoding='utf-8') as _file:
            yaml.dump(copy, _file, width=100000)

    @staticmethod
    def reach_attribute(where, attributes):
        """
            Fetches an attribute with the notation a.b.c.d
            Throws AttributeError if any level is not found
        """
        # get rid of special case
        if attributes is None or not attributes:
            return where

        result = None
        item = where
        attribute_list = attributes.split('.')
        if attribute_list[0] == 'config':
            attribute_list = attribute_list[1:]
        for attribute in attribute_list:
            index = re.findall(r'\[(\d*?)\]', attribute)
            if len(index):
                if len(index) > 1:
                    raise ValueError(f'unable to process multiple indexes: {attribute}')
                index = int(index[0])
                result = item[index]
            else:
                result = item[attribute]
            item = result
        return result

    @classmethod
    def assign_value(cls, where, attributes, value):
        """
            Sets an attribute with the notation a.b.c.d
        """
        item = where
        attribute_list = attributes.split('.')
        if len(attribute_list) > 1:
            item = cls.reach_attribute(where, '.'.join(attribute_list[:-1]))
        attribute = attribute_list[-1]
        index = re.findall(r'\[(\d*?)\]', attribute)
        if len(index):
            if len(index) > 1:
                raise ValueError(f'unable to process multiple indexes: {attribute}')
            index = int(index[0])
            item[index] = value
        else:
            item[attribute] = value

    @classmethod
    def parent(cls, attributes):
        """
            Returns the parent attribute
        """
        attrs = attributes.split('.')
        parent = attrs[:-1]
        return '.'.join(parent)

    @classmethod
    def generic_form(cls, attributes):
        """
            Returns the attributes without indexes for list:
            a.b.[0].c.[1].d -> a.b.[].c.[].d
        """
        lists = re.findall(r'\[\d*?\]', attributes)
        for var in lists:
            attributes = attributes.replace(var, '[]')
        return attributes
