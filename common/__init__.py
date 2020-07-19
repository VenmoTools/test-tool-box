class Singleton(type):

    def __init__(self, *args, **kwargs):
        self.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = super().__call__(*args, **kwargs)
        return self.__instance


if __name__ == '__main__':
    class Test(metaclass=Singleton):
        def __init__(self):
            print("init Test")


    a = Test()
    b = Test()
    Test()
    Test()
