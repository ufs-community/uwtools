from ..basic import traverse_structure


def stringify(structure):
    """
    Converts all basic elements of a structure into strings
    """
    return traverse_structure(structure, visitor)


def visitor(value):
    if isinstance(value, bool):
        return value
    return str(value)
