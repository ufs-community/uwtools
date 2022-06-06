

class Base:

    wildcards = {'*', '?', '['}

    def __init__(self, *args):
        pass

    def find_root(self, path):
        last = len(path)
        for i in range(len(path)):
            if path[i] == '/':
                last = i
            elif path[i] in self.wildcards:
                return path[:last]
        return path
