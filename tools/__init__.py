import logging


def unstable(func):
    def inner(*args, **kwargs):
        logging.warning("this function not stable yet or has a problem")
        return func(*args, **kwargs)

    return inner


def bug(name, cause):
    def bug_inner(func):
        def inner(*args, **kwargs):
            logging.error(f"`{name}` function has bugs cause by {cause} Do not use it until fixed")
            exit(1)

        return inner

    return bug_inner


def unimplemented(name):
    def bug_inner(func):
        def inner(*args, **kwargs):
            logging.error(f"`{name}` is unimplemented")
            exit(1)

        return inner

    return bug_inner
