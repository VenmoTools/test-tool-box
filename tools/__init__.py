import logging


def warn(func):
    def inner(*args, **kwargs):
        logging.warning("this function not stable yet or has a problem")
        return func(*args, **kwargs)

    return inner


def bug(name):
    def warrp(func):
        def inner(*args, **kwargs):
            raise SystemError(f"`{name}` function has bugs do not use it until fixed")

        return inner

    return warrp
