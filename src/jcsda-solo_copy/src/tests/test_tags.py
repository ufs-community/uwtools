from solo.tag import Tag

config = {
    'a': 'hello',
    'b': 'tag1::this is tag 1',
    'u': 'tag1::this is tag 1 and a half',
    'c': 'tag2::this is tag 2',
    'd': {
        '1': 'this is tag d.1',
        '2': 'this is not a tag'
    },
    'l': [
        'tag_list::item1',
        'item no tags',
        'tag_list::item2',
        'tag_list::item3',
        'item4 not a tag',
    ]
}


result_all = {'tag1': [('b', 'this is tag 1'), ('u', 'this is tag 1 and a half')],
              'tag2': [('c', 'this is tag 2')],
              'tag_list': [('l.[0]', 'item1'), ('l.[2]', 'item2'), ('l.[3]', 'item3')]}


def test_all_tags():
    t = Tag(config)
    assert t == result_all


def test_filter1():
    result = {'tag_list': [('l.[0]', 'item1'), ('l.[2]', 'item2'), ('l.[3]', 'item3')]}
    t = Tag(config, 'tag_list')
    assert t == result


def test_filter2():
    result = {'tag1': [('b', 'this is tag 1'), ('u', 'this is tag 1 and a half')],
              'tag_list': [('l.[0]', 'item1'), ('l.[2]', 'item2'), ('l.[3]', 'item3')]}
    t = Tag(config, 'tag_list', 'tag1')
    assert t == result


def test_filter_keep_all():
    t = Tag(config, 'tag_list', 'tag1', 'tag2')
    assert t == result_all
