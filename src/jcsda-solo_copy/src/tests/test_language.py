import os
import pytest
from solo.language import Directive


file_base = os.path.join(os.path.dirname(__file__), 'language')


class DirectiveTest(Directive):
    def __init__(self, *args, **kwargs):
        super().__init__(file_base, *args, **kwargs)


def test_basic_schema_ok():

    """
        Covering simple attributes
    """

    person = DirectiveTest(
        schema_name='person',
        name='Doe',
        first_names='John',
        employed='yes',
        education='bachelor',
        married=True,
        house_status='owner',
        age='42'
    )
    assert person.name == 'Doe'
    assert isinstance(person.first_names, list)
    assert person.employed is True
    assert person.education == 'bachelor'
    assert person.married is True
    assert person.house_status == 'owner'
    assert isinstance(person.age, int)


def test_basic_schema_required():

    """
        name is missing, an exception should be raised
    """

    ex = None
    with pytest.raises(SystemExit) as e:
        ex = e
        DirectiveTest(
            schema_name='person',
            first_names='John',
            employed='yes',
            house_status='owner',
            married=True,
            age=42
        )
    # Check that the field name is mentioned in the text of the exception
    assert repr(ex).find('name') != -1


def test_basic_schema_default_value():

    """
        education has a default value
    """

    person = DirectiveTest(
        schema_name='person',
        name='Doe',
        first_names='John',
        employed='yes',
        house_status='owner',
        age=42
    )
    assert person.education == 'postgrad'


def test_basic_schema_set_choices():

    """
        house_status can only be owner, mortgage or rental. If not, an exception
        should be raised.
    """

    ex = None
    with pytest.raises(SystemExit) as e:
        ex = e
        DirectiveTest(
            schema_name='person',
            name='Doe',
            first_names='John',
            employed='yes',
            house_status='car',
            age=42
        )
    assert repr(ex).find('house_status') != -1


def test_basic_schema_not_required():

    """
        married is not required, if missing, no exception should be raised.
    """

    DirectiveTest(
        schema_name='person',
        name='Doe',
        first_names='John',
        employed='yes',
        education='bachelor',
        house_status='owner',
        age='42'
    )


def test_basic_schema_alias():

    """
        first_names is aliased to firsts, check no exception is raised and
        the data comes back with first_names
    """

    person = DirectiveTest(
        schema_name='person',
        name='Doe',
        firsts='Bob',
        employed='yes',
        education='bachelor',
        married=True,
        house_status='owner',
        age='42'
    )
    assert 'first_names' in person
    assert person.first_names == ['Bob']


def test_basic_schema_unique():

    """
        name is declared unique. If we pass a list, an exception is raised.
    """

    ex = None
    with pytest.raises(SystemExit) as e:
        ex = e
        DirectiveTest(
            schema_name='person',
            name=['Doe', 'Robert'],
            firsts='Bob',
            employed='yes',
            education='bachelor',
            married=True,
            house_status='owner',
            age='42'
        )
    assert repr(ex).find('name') != -1


def test_basic_schema_inheritance():

    """
        Same as above but with the employee schema
    """

    person = DirectiveTest(
        schema_name='employee',
        name='Doe',
        first_names='John',
        employed='yes',
        education='bachelor',
        married=True,
        house_status='owner',
        age='42',
        department='sales'
    )
    assert person.name == 'Doe'
    assert isinstance(person.first_names, list)
    assert person.employed is True
    assert person.education == 'bachelor'
    assert person.married is True
    assert person.house_status == 'owner'
    assert isinstance(person.age, int)


def test_choices_inheritance():

    """
        Make sure validations occur after inheritance: department in invalid
    """

    ex = None
    with pytest.raises(SystemExit) as e:
        ex = e
        DirectiveTest(
            schema_name='employee',
            name='Doe',
            first_names='John',
            employed='yes',
            education='bachelor',
            married=True,
            house_status='owner',
            age='42',
            department='marketing'
        )
    assert repr(ex).find('department') != -1


def test_required_inheritance():

    """
        Make sure required fields are checked after inheritance: department is missing
    """

    ex = None
    with pytest.raises(SystemExit) as e:
        ex = e
        DirectiveTest(
         schema_name='employee',
         name='Doe',
         first_names='John',
         employed='yes',
         education='bachelor',
         married=True,
         house_status='owner',
         age='42',
        )
    assert repr(ex).find('department') != -1


def test_delete_inheritance1():

    """
        When inheriting a schema, field(s) from the parent can be removed (deleted)
        Here we delete house_status and insert it in the directive, an exception
        should be raised
    """

    ex = None
    with pytest.raises(SystemExit) as e:
        ex = e
        DirectiveTest(
         schema_name='neighbour',
         name='Doe',
         first_names='John',
         employed='yes',
         education='bachelor',
         married=True,
         house_status='owner',
         age='42',
        )
    assert repr(ex).find('house_status') != -1


def test_delete_inheritance2():

    """
        Same as test_delete_inheritance1, expect no exception as not inserting house_status
    """

    DirectiveTest(
        schema_name='neighbour',
        name='Doe',
        first_names='John',
        employed='yes',
        education='bachelor',
        married=True,
        age='42'
    )


def test_change_status_inheritance():
    """
        employee.yaml inherits the field married from person where it is not
        required and makes it required. By not including it, an exception
        should be raised.
    """
    ex = None
    with pytest.raises(SystemExit) as e:
        ex = e
        DirectiveTest(
         schema_name='employee',
         name='Doe',
         first_names='John',
         employed='yes',
         education='bachelor',
         #married=True,
         house_status='owner',
         age='42',
         department='sales'
        )
    assert repr(ex).find('married') != -1


def test_multiple_inheritance():

    """
        EmployeeGolfer inherits both from person and golfer
    """

    person = DirectiveTest(
        schema_name='employee_golfer',
        name='Doe',
        first_names='John',
        employed='yes',
        education='bachelor',
        married=True,
        house_status='owner',
        age='42',
        department='sales',
        handicap=42
    )
    assert person.name == 'Doe'
    assert isinstance(person.first_names, list)
    assert person.employed is True
    assert person.education == 'bachelor'
    assert person.married is True
    assert person.house_status == 'owner'
    assert isinstance(person.age, int)
    assert person.handicap == 42
    assert person.department == 'sales'


def test_multiple_inheritance_required():

    """
        Checking that the extra field (handicap) inherited from golfer is required
    """

    ex = None
    with pytest.raises(SystemExit)as e:
        ex = e
        DirectiveTest(
            schema_name='employee_golfer',
            name='Doe',
            first_names='John',
            employed='yes',
            education='bachelor',
            married=True,
            house_status='owner',
            age='42',
            department='sales'
        )
    assert repr(ex).find('handicap') != -1


def test_conditional_inheritance_1d1():
    DirectiveTest(
        schema_name='shape1',
        x=12,
        y=145,
        colour='yellow',
        radius=5
    )


def test_conditional_inheritance_1d2():
    DirectiveTest(
        schema_name='shape1',
        x=12,
        y=145,
        z=4,
        colour='yellow',
        radius=5,
        dimension='3d'
    )


def test_conditional_inheritance_2d1():
    DirectiveTest(
        schema_name='shape2',
        x=12,
        y=145,
        colour='yellow',
        radius=5,
        shape='circle',
        dimension='2d'
    )


def test_conditional_inheritance_2d2():
    DirectiveTest(
        schema_name='shape2',
        x=12,
        y=145,
        z=12,
        colour='yellow',
        length=17,
        width=13,
        shape='rectangle',
        dimension='3d'
    )


def test_conditional_inheritance_2d3():
    DirectiveTest(
        schema_name='shape2',
        x=12,
        y=145,
        z=12,
        colour='yellow',
        side=4,
        shape='square',
        dimension='3d'
    )


def test_conditional_inheritance_change_status():
    """
        in shape the default for colour is black, 3d_plus changes it to green
        in 3d_plus, an extra field dummy is introduced, unique. square_plus
        makes it not unique.
    """
    d = DirectiveTest(
        schema_name='shape2',
        x=12,
        y=145,
        z=12,
        side=4,
        shape='square_plus',
        dimension='3d_plus',
        dummy='hello'
    )
    assert d.colour == 'green'
    assert isinstance(d.dummy, list)


def test_lowercase():
    """
        in shape3 we set the colour to be forced to lowercase.
    """
    d = DirectiveTest(
        schema_name='shape3',
        x=12,
        y=145,
        z=12,
        side=4,
        shape='square',
        dimension='3d',
        colour='GREEN'
    )
    assert d.colour == 'green'


def test_uppercase():
    """
        in shape3 we set the colour to be forced to lowercase.
    """
    d = DirectiveTest(
        schema_name='shape4',
        x=12,
        y=145,
        z=12,
        side=4,
        shape='square',
        dimension='3d',
        colour='blue'
    )
    assert d.colour == 'BLUE'

def test_exclude_when():

    person = DirectiveTest(
        schema_name='person_exclude',
        name='Claude',
        first_names='John',
        education='bachelor',
        married=True,
        house_status='owner',
        age='42'
    )
