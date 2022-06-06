from solo.tree_search import TreeSearch


data = {
    'level1.level2.level3': 1,
    'level1.level2': 18,
    'level1.level2.level4': 8,
    'level1': 3,
    'level3': 4
}


def test_tree_search1():
    s = TreeSearch(data)
    assert s.match('level1.level2.level3') == 4

def test_tree_search2():
    s = TreeSearch(data)
    assert s.match('level3') == 4

def test_tree_search3():
    s = TreeSearch(data)
    assert s.match('level1.level2.level5') == 18

def test_tree_search4():
    s = TreeSearch(data)
    assert s.match('level1.level5') == 3

def test_tree_search5():
    s = TreeSearch(data)
    assert s.match('level1.level2') == 18

def test_tree_search6():
    s = TreeSearch(data)
    assert s.match('level1') == 3

def test_tree_search7():
    s = TreeSearch(data)
    assert s.match('level2') == None

