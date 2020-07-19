import abc
import itertools
import logging
import os
import queue
import threading
import weakref
from enum import Enum
from multiprocessing import Process, get_context
from multiprocessing.queues import SimpleQueue
from os import cpu_count
from threading import Thread
from typing import List, Tuple

import pytest


class State(Enum):
    INIT = "INIT"
    RUN = "RUN"
    CLOSE = "CLOSE"
    TERMINATE = "TERMINATE"


class EndSignal(Enum):
    END = 1


class Worker(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def initializer(self, args):
        pass

    @abc.abstractmethod
    def __call__(self, in_queue: SimpleQueue, out_queue: SimpleQueue, init_args, wrap_exception, *args, **kwargs):
        pass


class Task(metaclass=abc.ABCMeta):

    def __init__(self):
        self.can_call = False

    @abc.abstractmethod
    def args(self):
        pass

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class TaskHandler(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __call__(self, task_queue: SimpleQueue, pool: List[Process],
                 in_queue: SimpleQueue, out_queue: SimpleQueue, cache):
        pass


class ResultHandler(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def __call__(self, out_queue: SimpleQueue, cache):
        pass


class PytestResultHandler(ResultHandler):

    def __init__(self):
        logging.debug("[PytestResultHandler] start")

    def __call__(self, out_queue: SimpleQueue, cache):
        while True:
            res = out_queue.get()
            if res is EndSignal.END:
                break
            logging.debug(f"[PytestResultHandler] result `{res}`")

        logging.debug("[PytestResultHandler] exiting")


class PytestTaskHandler(TaskHandler):
    def __call__(self, task_queue: SimpleQueue, pool: List[Process], in_queue: SimpleQueue, out_queue: SimpleQueue,
                 cache):
        cur_th = threading.current_thread()

        while True:
            if cur_th._state != State.RUN:
                logging.debug('task handler found thread._state != RUN')
                break
            task = task_queue.get()
            if task is EndSignal.END:
                logging.debug("got exit signal")
                break
            assert isinstance(task, Task), "task must implement Task class"
            try:
                in_queue.put(task)
            except Exception as  e:
                logging.error(e)


class PytestTask(Task):

    def __init__(self):
        super().__init__()
        self._args = []
        self._plugins = []
        self.can_call = True

    def set_options(self, opt):
        if isinstance(opt, list):
            self._args.extend(opt)
        else:
            self._args.append(opt)
        return self

    def set_test_file(self):
        pass

    def set_plugins(self, plugins: list):
        self._plugins.extend(plugins)

    def args(self):
        return self._args, self._plugins

    def __call__(self, *args, **kwargs):
        pass


class PytestWorker(Worker):

    def initializer(self, args):
        pass

    def __init__(self):
        self._main = pytest.main
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S')

    def __call__(self, in_queue: SimpleQueue, out_queue: SimpleQueue, init_args, wrap_exception, *args, **kwargs):
        if init_args:
            self.initializer(init_args)
        while True:
            try:
                logging.debug("waiting recv task")
                task = in_queue.get()
                logging.debug("task received")
            except (EOFError, OSError):
                logging.debug('worker got EOFError or OSError -- exiting')
                break
            if task is None:
                logging.debug('worker got sentinel -- exiting')
                break
            p_args = task.args()
            if isinstance(p_args, Tuple):
                args_l, plugins = p_args
                exit_code = self._main(args_l, plugins)
            else:
                exit_code = self._main(p_args)
            try:
                out_queue.put(exit_code)
            except Exception as e:
                out_queue.put(e)


class CustomPool:
    _pool: List[Process]

    def __init__(self, processes=None, group=None, worker=PytestWorker,
                 task_worker=PytestTaskHandler, result_worker=PytestResultHandler):
        """
        创建进程池的初始化函数
        :param processes: 指定进程数
        :param group: 指定进程组
        :param worker: 指定使用的Worker
        :param task_worker:
        """
        self._pool = []  # 进程队列
        self._state = State.INIT  # 进程池状态
        logging.debug(f"pool state: {self._state}")
        self._processes = processes if processes else cpu_count()  # 指定进程池状态
        assert self._processes > 1  # 进程数必须大于1
        self._task_queue = queue.SimpleQueue()  # 任务队列
        self._ctx = group or get_context()
        self._in_queue, self._out_queue = self._init_queue()  # Worker 消息发送，接收队列
        self._change_notifier = self._ctx.SimpleQueue()  # 状态改变队列
        self._init_args = {}  # 初始化参数
        self._wrap_exception = None  # 是否需要处理异常
        self._worker = worker()  # 指定的Worker
        self._task_worker = task_worker()
        self._result_worker = result_worker()
        self._cache = {}
        logging.debug("queue init done!")
        assert isinstance(self._worker, Worker), f"worker `{worker.__class__}` not implement `Worker`"  # 必须集成Worker类
        try:
            self._repopulate_pool()  # 创建进程池
        except Exception:  # 在创建过程发生错误需要退出所有的进程
            for p in self._pool:
                if p.exitcode is None:
                    # 向进程发送信号结束
                    p.terminate()
            for p in self._pool:
                p.join()
            raise
        logging.debug("create process finished")
        # 专门用于监测所有子进程状态的线程
        logging.debug("start worker handler thread")
        self._workers_handler_th = Thread(
            target=CustomPool._handle_workers,
            args=(self._ctx, self._processes, self.Process, self._task_queue,
                  self._in_queue, self._out_queue, self._init_args, self._worker,
                  self._wrap_exception, self._change_notifier, self._pool)
        )
        self._set_daemon_and_start(self._workers_handler_th)
        logging.debug(f"worker handler thread start finished, is alive:{self._workers_handler_th.is_alive()}")

        # 专门用于处理任务的线程
        logging.debug("start task handler thread")
        self._handle_task_th = Thread(
            target=CustomPool._handle_task,
            args=(self._task_worker, self._task_queue, self._pool,
                  self._in_queue, self._out_queue, self._cache)
        )
        self._set_daemon_and_start(self._handle_task_th)
        logging.debug(f"task handler thread start finished, is alive:{self._workers_handler_th.is_alive()}")

        # 专门用于处理进程返回结果的线程
        logging.debug("start result handler thread")
        self._handle_result_th = Thread(
            target=CustomPool._handle_result,
            args=(self._result_worker, self._out_queue, self._cache)
        )
        self._set_daemon_and_start(self._handle_result_th)
        logging.debug(f"result handler thread start finished, is alive:{self._workers_handler_th.is_alive()}")

        # 进程终结
        logging.debug("create terminate guards")
        self._terminate = Finalize(
            self, self._terminate_pool,
            args=(self._task_queue, self._in_queue, self._out_queue, self._pool,
                  self._change_notifier, self._workers_handler_th, self._handle_task_th,
                  self._handle_result_th),
            exitpriority=15
        )
        self._state = State.RUN
        logging.debug(f"pool state is:{self._state}")

    @staticmethod
    def _set_daemon_and_start(th: Thread):
        """
        设置成守护线程后运行
        :param th: 运行的进程
        :return:
        """
        th.setDaemon(True)
        th._state = State.RUN
        th.start()

    # @stable
    # @since 1.0
    def get_all_pid(self) -> List[int]:
        """
        返回所有进程的pid
        :return:
        """
        return [p.pid for p in self._pool]

    # @stable
    # @since 1.0
    @staticmethod
    def _terminate_pool(_task_queue: SimpleQueue, _in_queue: SimpleQueue, out_queue: SimpleQueue,
                        pool: List[Process], change_notifier: SimpleQueue,
                        worker_handler_th: Thread, handle_task_th: Thread, handle_result_th: Thread
                        ):
        """
        终止进程池
        :param _task_queue: 暂不使用
        :param _in_queue: 暂不使用
        :param out_queue: 通知结束进程
        :param pool: 进程池
        :param change_notifier: 通知状态改变
        :param worker_handler_th: worker管理进程
        :param handle_task_th: 任务管理进程
        :param handle_result_th: 执行结果管理进程
        :return:
        """
        worker_handler_th._state = State.TERMINATE
        handle_task_th._state = State.TERMINATE

        assert handle_result_th.is_alive(), "result handler not alive"
        handle_result_th._state = State.TERMINATE

        # 发送终止信号
        change_notifier.put(EndSignal.END)
        out_queue.put(EndSignal.END)

        # 等待检测进程的线程退出
        if threading.current_thread() != worker_handler_th:
            worker_handler_th.join()

        # 向进程池中的所有进程发送终止信号
        if pool:
            for p in pool:
                if p.exitcode is None:
                    p.terminate()

        # 等待任务处理线程退出
        if threading.current_thread() != handle_task_th:
            handle_task_th.join()

        # 等待处理结果线程退出
        if threading.current_thread() != handle_result_th:
            handle_result_th.join()

        # 等待所有存活的进程退出
        if pool:
            for p in pool:
                if p.is_alive():
                    p.join()

    def __repr__(self):
        cls = self.__class__
        return (f'<{cls.__module__}.{cls.__qualname__} '
                f'state={self._state} '
                f'Worker={self._worker.__class__}'
                f'pool_size={len(self._pool)}>')

    @classmethod
    def _handle_workers(cls, ctx,
                        processes: int, Proc, task_queue: SimpleQueue,
                        in_queue: SimpleQueue,
                        out_queue: SimpleQueue,
                        init_args, worker: Worker,
                        wrap_exception, change_notifier: SimpleQueue, pool: List[Process]):
        """
        管理进程池中的所有进程，在线程中执行
        :param ctx: 进程上下文
        :param processes: 指定的进程数量
        :param Proc: 用于创建进程，使用get_context()完成
        :param in_queue: 将任务发送给进程
        :param out_queue: 从执行完的进程获取数据
        :param init_args: 初始化数据
        :param worker: 指定的Worker
        :param wrap_exception: 是否需要包裹任务执行异常
        :return:
        """
        cur_th = threading.current_thread()
        while cur_th._state == State.RUN:
            cls._maintain_pool(ctx, processes, Proc, in_queue, out_queue, init_args, worker, wrap_exception, pool)
            cls._wait_for_updates(change_notifier)
        # exit thread
        logging.debug("send exit signal to task queue")
        task_queue.put(EndSignal.END)

    @staticmethod
    def _wait_for_updates(change_notifier: SimpleQueue):
        """
        该方法会阻塞线程等待不断从change_notifier取出内容
        :param change_notifier:
        :return:
        """
        # sentinels, timeout,
        # wait(sentinels, timeout=timeout)
        while not change_notifier.empty():
            res = change_notifier.get()
            logging.debug(f"got signal, content: {res}")

    @classmethod
    def _maintain_pool(cls, ctx,
                       processes: int, Proc,
                       in_queue: SimpleQueue,
                       out_queue: SimpleQueue,
                       init_args, worker: Worker,
                       _wrap_exception, pool: List[Process]):
        """
        管理进程池
        :param ctx: 进程上下文
        :param processes: 指定的进程数量
        :param Proc: 用于创建进程，使用get_context()完成
        :param in_queue: 将任务发送给进程
        :param out_queue: 从执行完的进程获取数据
        :param init_args: 初始化数据
        :param worker: 指定的Worker
        :param _wrap_exception: 是否需要包裹任务执行异常
        :param pool: 进程池
        :return:
        """
        # 检测并处理已经完成的任务进程
        if cls._terminate_exited_process(pool):
            # 如果有已经完成的进程，结束后重新创建新的进程，保持进程的是满的
            cls._repopulate_pool_static(
                ctx, Proc, processes, pool, in_queue, worker, out_queue, init_args, _wrap_exception
            )

    @classmethod
    def _terminate_exited_process(cls, pool: List[Process]) -> bool:
        """
        清除进程池中所有已退出的进程
        :param pool: 进程池
        :return: 如果清除了进程返回True否则返回False
        """
        has__terminated = False
        for i in reversed(range(len(pool))):
            worker = pool[i]
            if worker.exitcode is not None:
                # worker exited
                worker.join()
                has__terminated = True
                del pool[i]
        return has__terminated

    @classmethod
    def _handle_result(cls, handle_result: ResultHandler, out_queue: SimpleQueue, cache):
        handle_result(out_queue, cache)

    @classmethod
    def _handle_task(cls, handler: TaskHandler, task_queue: SimpleQueue, pool: List[Process],
                     in_queue: SimpleQueue, out_queue: SimpleQueue, cache):
        handler(task_queue, pool, in_queue, out_queue, cache)

    def _check_running(self):
        """
        检查进程池状态是否在运行
        :return:
        """
        if self._state != State.RUN:
            raise ValueError("Pool not running")

    def apply_async(self, task: Task):
        """
        提交执行任务
        :param task:
        :return:
        """
        self._check_running()
        self._task_queue.put(task)

    def _init_queue(self):
        """
        初始化发送和接收队列
        :return:
        """
        return self._ctx.SimpleQueue(), self._ctx.SimpleQueue()

    def _repopulate_pool(self):
        """
        对比设置的进程数与当前进程池的数量，创建不足的数量进程
        :return:
        """
        logging.debug(f"create {self._processes} processes")
        return self._repopulate_pool_static(self._ctx, self.Process,
                                            self._processes,
                                            self._pool, self._in_queue, self._worker,
                                            self._out_queue,
                                            self._init_args,
                                            self._wrap_exception)

    @staticmethod
    def _repopulate_pool_static(ctx, Proc, processes, pool, in_queue, worker,
                                out_queue, init_args, wrap_exception):
        """
        对比设置的进程数与当前进程池的数量，创建不足的数量进程
        例如指定创建10个进程，当前为0个进程则创建10个进程
        如果指定创建10个进程，因为部分进程执行完退出只剩下4个，则创建6个
        :param ctx: 进程上下文
        :param processes: 指定的进程数量
        :param Proc: 用于创建进程，使用get_context()完成
        :param in_queue: 将任务发送给进程
        :param out_queue: 从执行完的进程获取数据
        :param init_args: 初始化数据
        :param worker: 指定的Worker
        :param wrap_exception: 是否需要包裹任务执行异常
        :return:
        """
        for i in range(processes - len(pool)):
            w = Proc(ctx, target=worker,
                     args=(in_queue, out_queue,
                           init_args,
                           wrap_exception))
            w.name = w.name.replace('Process', 'PoolWorker')
            w.daemon = True
            w.start()
            logging.debug(f"{w.name} start, is alive: {w.is_alive()}")
            pool.append(w)

    @staticmethod
    def Process(ctx, *args, **kwargs):
        """
        根据当前的上下文创建进程
        :param ctx: 上下文
        :param args: 创建进程参数
        :param kwargs: 创建进程参数
        :return:
        """
        return ctx.Process(*args, **kwargs)

    # @stable
    # @since 1.0
    def close(self):
        """
        发送关闭信号到进程池中的所有进程，该方法不会理解结束所有进程
        如果需要终止所有进程需要先调用 terminate或close方法然后调用join函数
        :return:
        """
        logging.info("cloning pool")
        if self._state == State.RUN:
            self._state = State.CLOSE
            logging.debug(f"pool state: {self._state}")
            self._workers_handler_th._state = State.CLOSE
            logging.debug("send terminate signal")
            self._change_notifier.put(EndSignal.END)

    # @stable
    # @since 1.0
    def join(self):
        """
        结束整个进程池，如果进程池没有调用close或terminate方法则会抛出ValueError
        :return:
        """
        if self._state == State.RUN:
            raise ValueError("Pool is still running")
        elif self._state not in (State.CLOSE, State.TERMINATE):
            raise ValueError("In unknown state")
        logging.debug("[Waiting workers] handler thread")
        self._workers_handler_th.join()
        logging.debug("[Workers handler] thread exited")

        logging.debug("[Task handler] thread")
        self._handle_task_th.join()
        logging.debug("[Task handler] thread exited")

        logging.debug("[Result Handler] handler thread")
        self._handle_result_th.join()
        logging.debug("[Result Handler] thread exited")

        for p in self._pool:
            logging.debug(f"[{p.name}] waiting  process")
            p.join()
            logging.debug(f"[{p.name}] process exited")

    # @stable
    # @since 1.0
    def terminate(self):
        """
        向所有进程发送结束信号
        :return:
        """
        logging.debug('terminating pool')
        self._state = State.TERMINATE
        self._workers_handler_th._state = State.TERMINATE
        self._change_notifier.put(EndSignal.END)
        self._terminate()


# ============== Copy Form multiprocessing utils module =============================
_finalizer_registry = {}
_finalizer_counter = itertools.count()


class Finalize(object):
    """
    Class which supports object finalization using weakrefs
    """

    def __init__(self, obj, callback, args=(), kwargs=None, exitpriority=None):
        if (exitpriority is not None) and not isinstance(exitpriority, int):
            raise TypeError(
                "Exitpriority ({0!r}) must be None or int, not {1!s}".format(
                    exitpriority, type(exitpriority)))

        if obj is not None:
            self._weakref = weakref.ref(obj, self)
        elif exitpriority is None:
            raise ValueError("Without object, exitpriority cannot be None")

        self._callback = callback
        self._args = args
        self._kwargs = kwargs or {}
        self._key = (exitpriority, next(_finalizer_counter))
        self._pid = os.getpid()

        _finalizer_registry[self._key] = self

    def __call__(self, wr=None,
                 # Need to bind these locally because the globals can have
                 # been cleared at shutdown
                 _finalizer_registry=_finalizer_registry,
                 getpid=os.getpid):
        """
        Run the callback unless it has already been called or cancelled
        """
        try:
            del _finalizer_registry[self._key]
        except KeyError:
            logging.debug('finalizer no longer registered')
        else:
            if self._pid != getpid():
                logging.debug('finalizer ignored because different process')
                res = None
            else:
                logging.debug('finalizer calling %s with args %s and kwargs %s',
                              self._callback, self._args, self._kwargs)
                res = self._callback(*self._args, **self._kwargs)
            self._weakref = self._callback = self._args = \
                self._kwargs = self._key = None
            return res

    def cancel(self):
        """
        Cancel finalization of the object
        """
        try:
            del _finalizer_registry[self._key]
        except KeyError:
            pass
        else:
            self._weakref = self._callback = self._args = \
                self._kwargs = self._key = None

    def still_active(self):
        """
        Return whether this finalizer is still waiting to invoke callback
        """
        return self._key in _finalizer_registry

    def __repr__(self):
        try:
            obj = self._weakref()
        except (AttributeError, TypeError):
            obj = None

        if obj is None:
            return '<%s object, dead>' % self.__class__.__name__

        x = '<%s object, callback=%s' % (
            self.__class__.__name__,
            getattr(self._callback, '__name__', self._callback))
        if self._args:
            x += ', args=' + str(self._args)
        if self._kwargs:
            x += ', kwargs=' + str(self._kwargs)
        if self._key[0] is not None:
            x += ', exitpriority=' + str(self._key[0])
        return x + '>'


def _run_finalizers(minpriority=None):
    """
    Run all finalizers whose exit priority is not None and at least minpriority

    Finalizers with highest priority are called first; finalizers with
    the same priority will be called in reverse order of creation.
    """
    if _finalizer_registry is None:
        # This function may be called after this module's globals are
        # destroyed.  See the _exit_function function in this module for more
        # notes.
        return

    if minpriority is None:
        f = lambda p: p[0] is not None
    else:
        f = lambda p: p[0] is not None and p[0] >= minpriority

    # Careful: _finalizer_registry may be mutated while this function
    # is running (either by a GC run or by another thread).

    # list(_finalizer_registry) should be atomic, while
    # list(_finalizer_registry.items()) is not.
    keys = [key for key in list(_finalizer_registry) if f(key)]
    keys.sort(reverse=True)

    for key in keys:
        finalizer = _finalizer_registry.get(key)
        # key may have been removed from the registry
        if finalizer is not None:
            logging.debug('calling %s', finalizer)
            try:
                finalizer()
            except Exception:
                import traceback
                traceback.print_exc()

    if minpriority is None:
        _finalizer_registry.clear()


# ============== Copy Form multiprocessing utils module =============================


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S')
    p = CustomPool()

    p.apply_async(PytestTask().set_options(["tests", "-s", "--tb=no"]))

    p.terminate()
    p.close()
    p.join()
