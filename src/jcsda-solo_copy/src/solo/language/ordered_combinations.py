from itertools import combinations


class OrderedCombinations:

    """
        generate combinations of the elements of the list in the order of the
        list. Examples:
        OrderedCombinations.generate(['a']) --> ['a']
        OrderedCombinations.generate(['a','b']) -->
           ['a_b']
           ['a', 'b']
        OrderedCombinations.generate(['a','b', 'c']) -->
          ['a_b_c']
          ['a', 'b_c']
          ['a_b', 'c']
          ['a', 'b', 'c']
        etc...

        This is used for the specializations of schemas in Language where, if there
        are 3 schemas being merged, a, b and c:
        - the schema a_b_c will be searched first (most specialised)
        - then a and b_c
        - then a_b and c
        - then a and b and c (three separate ones, should be the usual case)
        generates returns a list of combinations of names:
        [['a_b_c'], ['a', 'b_c'], ['a_b', 'c'], ['a', 'b', 'c']]
    """

    @staticmethod
    def cut(sequence, indexes):
        last = 0
        for i in indexes:
            yield sequence[last:i]
            last = i
        yield sequence[last:]

    @classmethod
    def generate_one(cls, sequence, count):
        for indexes in combinations(list(range(1, len(sequence))), count - 1):
            yield list(cls.cut(sequence, indexes))

    @classmethod
    def generate_all(cls, sequence):
        combs = []
        for i in range(1, len(sequence) + 1):
            for g in cls.generate_one(sequence, i):
                combs.append(g)
        result = []
        for item in combs:
            name = []
            for v in item:
                name.append('_'.join(v))
            result.append(name)
        return result

    @classmethod
    def find_schemas(cls, sequence, schema_reader):
        for i in range(1, len(sequence) + 1):
            found_schemas = []
            for combination in cls.generate_one(sequence, i):
                schemas = ['_'.join(x) for x in combination]
                for schema in schemas:
                    if schema_reader.schema_exists(schema):
                        found_schemas.append(schema)
            if len(found_schemas):
                return found_schemas
        return None
