import hashlib


class CheckSum:

    """
        Some checksum utilities.
    """

    @staticmethod
    def update_file(filename, check_sum, chunk_size=104857600):  # 100MB
        with open(filename, 'rb') as f:
            buffer = f.read(chunk_size)
            while len(buffer):
                check_sum.update(buffer)
                buffer = f.read(chunk_size)
        return check_sum

    @classmethod
    def calculate_file(cls, filename, chunk_size=104857600, method='sha256'):
        check_sum = getattr(hashlib, method)()
        return cls.update_file(filename, check_sum, chunk_size)

    @classmethod
    def calculate_file_iter(cls, filenames, chunk_size=104857600, method='sha256'):
        check_sum = getattr(hashlib, method)()
        for filename in filenames:
            check_sum = cls.update_file(filename, check_sum, chunk_size)
        return check_sum

    @staticmethod
    def update_str(string, check_sum):
        check_sum.update(bytearray(string.encode()))
        return check_sum

    @classmethod
    def calculate_str(cls, string, method='sha256'):
        check_sum = getattr(hashlib, method)()
        return cls.update_str(string, check_sum)

    @classmethod
    def calculate_iter(cls, iterator, method='sha256'):
        check_sum = getattr(hashlib, method)()
        for s in iterator:
            check_sum = cls.update_str(s, check_sum)
        return check_sum
