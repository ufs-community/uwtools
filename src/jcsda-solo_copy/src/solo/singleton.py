

class Singleton:

    """
        Inherit from this class to write a singleton. A singleton is a class with only
        one instance, if you instantiate again, it returns the first instance. Please
        note that with this implementation, the constructor is called again when you
        'instantiate' it again, so be careful about what you do in the constructor,
        use class variables instead.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
