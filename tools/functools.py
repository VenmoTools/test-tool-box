class FunctionManager:

    def __init__(self, clazz=None):
        self.func_class = clazz

    def get(self, func_name: str):
        """
        根据函数名获取函数
        :param func_name: 函数名
        :return:
        """
        try:
            return getattr(self.func_class, func_name)
        except AttributeError:
            try:
                return getattr(self, func_name)
            except AttributeError:
                raise ValueError("函数：【{}】没有被注册".format(func_name))

    def get_func_varnames(self, func_name: str):
        """
        获取函数的所有参数名
        :param func_name:
        :return:
        """
        code = self.get(func_name).__code__
        return [code.co_varnames[index] for index in range(code.co_argcount)]

    def register_function(self, func):
        """
        注册函数
        :param func:函数
        :return:
        """
        setattr(self, func.__name__, func)

    def all_functions(self):
        """
        获取所有已注册的函数
        :return:
        """
        return [self.__dict__[k].__name__ for k in self.__dict__ if k != "func_class"]
