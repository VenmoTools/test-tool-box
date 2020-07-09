import logging
import sys
import time
from collections.abc import Callable
from functools import wraps, partial
from inspect import signature


def time_it(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time_ns()
        res = func(*args, **kwargs)
        end = time.time_ns()
        logging.debug(f"{func.__name__} total time :{(end - start) / 1000 / 1000}s")
        return res

    return wrapper


def attach_wrapper(obj, func=None):
    if func is None:
        return partial(attach_wrapper, obj)
    setattr(obj, func.__name__, func)
    return func


def log(level=logging.INFO, name=None, message=None):
    def decorate(func):
        log_name = name if name else func.__module__
        lg = logging.getLogger(log_name)
        msg = message if message else func.__name__

        @wraps(func)
        def wrapper(*args, **kwargs):
            lg.log(level, msg)
            return func(*args, **kwargs)

        @attach_wrapper(wrapper)
        def set_level(n_level):
            nonlocal level
            level = n_level

        @attach_wrapper(wrapper)
        def set_message(n_msg):
            nonlocal msg
            msg = n_msg

        return wrapper

    return decorate


def callback(c_back=None, *f_args, **f_kwargs):
    def decorate(func):
        exception_handle = lambda x: logging.error(f"an {repr(x)} occurred when call \
`{func.__module__}.{func.__name__}` callback `{c_back.__module__}.{c_back.__name__}`", exc_info=sys.exc_info())

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                res = func(*args, **kwargs)
                c_back(res, *f_args, **f_kwargs)
                return res
            except Exception as e:
                if exception_handle is not None and isinstance(exception_handle, Callable):
                    exception_handle(e)

        @attach_wrapper(wrapper)
        def set_exception_handler(expt_func):
            nonlocal exception_handle
            exception_handle = expt_func

        return wrapper

    return decorate


def type_check(*ty_args, **ty_kwargs):
    def decorate(func):
        func_sig = signature(func)
        bound = func_sig.bind_partial(*ty_args, **ty_kwargs).arguments

        @wraps(func)
        def wrapper(*args, **kwargs):
            bound_value = func_sig.bind(*args, **kwargs)
            for name, v in bound_value.arguments.items():
                if name in bound:
                    if bound[name] is not None and not isinstance(v, bound[name]):
                        raise TypeError(f"Argument {name} must be {bound[name]}")

            func(*args, **kwargs)

        return wrapper

    return decorate


if __name__ == '__main__':
    def show_res(res):
        print(res)
        raise KeyError()


    @time_it
    @log()
    @callback(show_res)
    def test_add():
        a = 0
        for i in range(100000):
            a += i
        return a


    @type_check(x=int, y=int)
    def add(x, y=None):
        return x + 1


    logging.basicConfig(level=logging.DEBUG)
    test_add()
    test_add.set_message("call function")
    test_add.set_level(logging.INFO)
    test_add()
    ty, info, value = sys.exc_info()
    print(ty, info, value)

    add(5, "abcv")
