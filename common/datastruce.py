class ImmutableDict:
    """
    不可变类型字典
    """

    def __init__(self, **kwargs):
        self.__data = kwargs

    def __setitem__(self, key, value):
        raise ValueError("Can not change immutable dict items")

    def __getitem__(self, item):
        return self.__data[item]


class Context:
    """
    上下文，用于在不同的类和函数中传递值
    """

    def __init__(self):
        self.__immutable = ImmutableDict()

    def set(self, key, value):
        self.__immutable[key] = value

    def get(self, key):
        return self.__immutable[key]


class Response:
    """
    响应结果保存
    """

    def __init__(self):
        self.__response_table = ImmutableDict()

    def set(self, key, value):
        self.__response_table[key] = value

    def get(self, item):
        return self.__response_table[item]
