import pytest
from solo.factory import create_factory, Factory


def class_1():
    def internal():
        return '1'
    return internal


def class_2():
    def internal():
        return '2'
    return internal


def class_default():
    def internal():
        return 'default'
    return internal


def test_create_factory():
    create_factory('Testing1')
    try:
        from solo.factory import Testing1Factory
    except ModuleNotFoundError:
        raise AssertionError('factory was not added to the module')


def test_register_factory_with_default():
    factory = create_factory('Testing2')
    factory.register('class1', class_1)
    factory.register('class2', class_2)
    factory.register_default(class_default)

    action = factory.create('class1')
    assert action() == '1'
    action = factory.create('class2')
    assert action() == '2'
    action = factory.create('unknown')
    assert action() == 'default'


def test_register_factory_without_default():
    factory = create_factory('Testing3')
    factory.register('class1', class_1)
    factory.register('class2', class_2)

    action = factory.create('class1')
    assert action() == '1'
    action = factory.create('class2')
    assert action() == '2'
    with pytest.raises(IndexError):
        factory.create('unknown')


def test_is_registered():
    factory = create_factory('Testing4')
    factory.register('class1', class_1)
    factory.register('class2', class_2)
    factory.register_default(class_default)

    assert factory.is_registered('class1')
    assert factory.is_registered('class2')


def test_registered_list():
    factory = create_factory('Testing5')
    factory.register('class1', class_1)
    factory.register('class2', class_2)
    factory.register_default(class_default)

    assert factory.registered() == {'class1', 'class2'}


def test_import_factory():
    factory = create_factory('Testing6')
    from solo.factory import Testing6Factory

    assert factory == Testing6Factory


def test_get_factory():
    factory = create_factory('Testing7')
    my_factory = Factory.get_factory('Testing7Factory')

    assert factory == my_factory
