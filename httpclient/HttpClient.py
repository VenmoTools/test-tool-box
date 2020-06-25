import logging
import re
from datetime import timedelta
from threading import Lock

import requests
from requests.adapters import HTTPAdapter
from requests.cookies import extract_cookies_to_jar
from requests.hooks import dispatch_hook, default_hooks
from requests.sessions import preferred_clock
from requests.structures import CaseInsensitiveDict
from requests.utils import get_encoding_from_headers

from httpclient.convey import Convey
from httpclient.strcutures import ResponseMixin, RandomUserAgentMixin, RequestMixin, WithContext, \
    NoEnableCacheRequest, text2dict
from httpclient.strcutures import dict2text


class UpgradeResponse(requests.Response, ResponseMixin):

    @property
    def text(self):
        if not self.encoding:
            self.encoding = self.charset
        return super().text


class Adapter(HTTPAdapter):

    def build_response(self, req, resp) -> UpgradeResponse:
        response = UpgradeResponse()

        response.status_code = getattr(resp, 'status', None)

        response.headers = CaseInsensitiveDict(getattr(resp, 'headers', {}))

        response.encoding = get_encoding_from_headers(response.headers)
        response.raw = resp
        response.reason = response.raw.reason

        if isinstance(req.url, bytes):
            response.url = req.url.decode('utf-8')
        else:
            response.url = req.url

        extract_cookies_to_jar(response.cookies, req, resp)

        response.request = req
        response.connection = self

        return response


class ClientMixin:
    __slots__ = ()

    def do_request(self, method=None, url=None, headers=None, body=None, file=None, json=None):
        """
        client = HttpClient()

        @client.do_request(url="http://www.baidu.com", method="GET")
        def handler(response):
            print(response.text)

        response_body = handler()

        re_result = handler.regex(".*id=\"(\d\w)+?\"")

        :param json:
        :param file:
        :param method:
        :param url:
        :param headers:
        :param body:
        :return:
        """
        result = self.do(url).with_headers(headers).with_body(body, file, json).with_method(method).result

        def handle(func):
            def inner():
                nonlocal result  # 声明result不是本地变量，寻找result变量
                func.regex = lambda reg: re.findall(reg, result)

                return func(result)

            return inner

        return handle

    def check_cache(self):
        if not hasattr(self, "req"):
            raise NoEnableCacheRequest("请在实例化Client类时指定cache=True")

    def disable_random_ua(self):
        """
        关闭随机UA
        :return:
        """
        if hasattr(self, "req"):
            self.req.disable_random_ua()
        return self

    def enable_random_ua(self):
        """
        启用随机UA
        :return:
        """
        self.req.enable_random_ua()
        return self

    def reset(self):
        if hasattr(self, "times") and hasattr(self, "req"):
            delattr(self, "times")
        return self

    def do(self, url):
        """
        请求HTTP路径
        :param url:
        :return:
        """
        self.do_with_query(url, None)
        return self

    def _increment(self):
        if hasattr(self, "times"):
            try:
                self.lock.acquire()
                self.times += 1
                if self.times > 2:
                    logging.warning("检测到连续添加到body次数过多，请使用with_body/with_post_body添加")
            except Exception:
                pass
            finally:
                self.lock.release()

    def with_headers(self, header: dict):
        self.check_cache()
        self.req.prepare_headers(header)
        return self

    def with_text_header(self, header: str):
        """
        使用文本形式的Header
        语法格式为:
            Header键(Header值)
            如果有多个Header值使用`|`分割
        例如：
            Cookie(PHPSESSID=ototlqt0uuhr2ejhrnlfqv6fsq)|Accept(text/html,application/xhtml+xml,*/*;q=0.8)
            表示
            {
                "PHPSESSID": "ototlqt0uuhr2ejhrnlfqv6fsq",
                "Accept":"text/html,application/xhtml+xml,*/*;q=0.8"
            }
        c = HttpClient()
        c.do("http://192.168.1.24/login").with_text_header("Cookie(PHPSESSID=ototlqt0uuhr2ejhrnlfqv6fsq)|Accept(text/html,application/xhtml+xml,*/*;q=0.8)")
        :param header:
        :return:
        """
        self.check_cache()
        self.req.parser(header)
        return self

    def with_data(self, data):
        """

        :param data:
        :return:
        """
        self.check_cache()
        self._increment()
        self.req.prepare_body(data, None)
        return self

    def with_post_text_body(self, data):
        """
        使用字符串的形式传递参数
        例如：
            c = HttpClient()
            c.do("http://192.168.1.24/login").with_post_text_body("user=admin&password=123456").result
        :param data:
        :return:
        """
        return self.with_data(text2dict(data))

    def do_with_query(self, url, query):
        """
        使用带有查询的url
        例如：
            http://192.168.1.24/page?p=15&index=12
        请求：
            文本形式
            client = HttpClient()
            client.do_with_query(" http://192.168.1.24/page","p=15&index=12").result

            字典形式
            param = {
                "p":15,
                "index":12,
            }
            client = HttpClient()
            client.do_with_query(" http://192.168.1.24/page",param).result

        :param url:
        :param query:
        :return:
        """
        if isinstance(query, dict):
            query = dict2text(query)

        self.check_cache()
        setattr(self, "times", 0)
        self.req.prepare_url(url, query)
        return self

    def with_json(self, data):
        """
        使用Json数据请求
        :param data: json数据
        :return:
        """
        if not isinstance(data, dict):
            raise ValueError("`data` is not json object")

        self.check_cache()
        self._increment()
        self.req.prepare_body(data, None)
        return self

    def with_method(self, method):
        """
        使用指定的请求方式发送请求
        :param method:
        :return:
        """
        self.req.prepare_method(method)
        return self

    def with_file(self, filename):
        """
        上传文件
        :param filename: 文件路径
        :return:
        """
        self.with_stream(open(filename, "rb"))
        return self

    def with_stream(self, file_stream):
        """
        使用字节流形式
        :param file_stream: 二进制字节流
        :return:
        """
        self.check_cache()
        self._increment()
        self.req.prepare_body(None, file_stream)
        return self

    def with_body(self, data, file, js):
        """
        可以同时使用数据，文件，json形式
        :param data:
        :param file:
        :param js:
        :return:
        """
        self.check_cache()
        self.req.prepare_body(data, file, js)
        return self

    def with_post_body(self, data, file, js):
        """
        可以同时使用数据，文件，json形式，以post方法发送
        :param data:
        :param file:
        :param js:
        :return:
        """
        self.req.prepare_method("POST")
        self._increment()
        return self.req.prepare_body(data, file, js)

    def with_post_text(self, data):
        """
        使用字符串的形式传递参数
        例如：
            c = HttpClient()
            c.do("http://192.168.1.24/login").with_text_param("user=admin&password=123456").result
        :param data:
        :return:
        """
        self.check_cache()
        self._increment()
        self.req.prepare_method("POST")
        return self.with_post_text_body(data)

    def with_post_json(self, js):
        """
        使用post方法，请求体格式为json来发送请求
        :param js:
        :return:
        """
        self.check_cache()
        self._increment()
        self.req.prepare_method("POST")
        return self.with_json(js)

    def add_hooks(self, hook_name: str, hook):
        """
        添加回调函数，添加完回调函数后需要手动指定需要哪些函数需要调用
        :param hook_name:
        :param hook:
        :return:
        """
        if hook_name == 'response':
            logging.warning("do not use hooks named `response` this will ignore")
            return self
        self.req.add_hooks(hook_name, hook)
        return self

    def dispatch_hooks(self, hooks: str):
        """
        指定需要调用的回调函数

        # hooks基本的参数如下
        def callback(response,immutable_dict):
            pass
        response: 请求完毕后的响应结果
        params: 请求参数
        :param hooks: list or string
        :return:
        """
        has_instance = False
        if isinstance(hooks, str) and self.req.hooks.get(hooks):
            self._dispatch_hooks.append(hooks)
            has_instance = True
        if isinstance(hooks, list):
            self._dispatch_hooks.extend(hooks)
            has_instance = True
        if not has_instance:
            logging.warning(f"`{hooks}` not found, make sure you add hooks by `add_hooks` method")
        return self

    def response_hooks(self, hooks):
        """
        该回调函数会自动执行，并且会修改请求参数和响应结果
        :param hooks:
        :return:
        """
        self.req.hooks["response"] = hooks
        return self

    @property
    def result(self) -> UpgradeResponse:
        """
        发生HTTP请求并获取结果
        :return:
        """
        self.check_cache()
        self.reset()
        if hasattr(self.req, "ua") and self.req.ua:
            ua = {"User-Agent": next(self.req.random())}
            if self.req.headers:
                self.req.headers.update(ua)
            else:
                self.req.headers = ua
        resp = self.send(self.req)
        return resp

    def http_except(self, case) -> Convey:
        """
        可以结合unittest进行响应断言
        :param case:
        :return:
        """
        return Convey(case).set_response(self.result)


@WithContext
class HttpClient(requests.Session, ClientMixin):

    def __init__(self):
        super().__init__()
        self.lock = Lock()
        self.mount('https://', Adapter())
        self.mount('http://', Adapter())
        self.req = HttpRequest().reset_all()
        self._dispatch_hooks = []

    def send(self, request, **kwargs) -> UpgradeResponse:
        kwargs.setdefault('stream', self.stream)
        kwargs.setdefault('verify', self.verify)
        kwargs.setdefault('cert', self.cert)
        kwargs.setdefault('proxies', self.proxies)

        if isinstance(request, requests.Request):
            raise ValueError('You can only send PreparedRequests.')
        if isinstance(request, HttpRequest):
            request.check()
        allow_redirects = kwargs.pop('allow_redirects', True)
        hooks = request.hooks

        adapter = self.get_adapter(url=request.url)

        start = preferred_clock()

        r = adapter.send(request, **kwargs)

        elapsed = preferred_clock() - start
        r.elapsed = timedelta(seconds=elapsed)

        # this function not change response and result params
        if len(self._dispatch_hooks) > 0:
            dispatch(self._dispatch_hooks, hooks, r, **kwargs)

        # dispatch hook will change response and request params
        r = dispatch_hook('response', hooks, r, **kwargs)

        if r.history:
            for resp in r.history:
                extract_cookies_to_jar(self.cookies, resp.request, resp.raw)

        extract_cookies_to_jar(self.cookies, request, r.raw)

        gen = self.resolve_redirects(r, request, **kwargs)

        history = [resp for resp in gen] if allow_redirects else []

        if history:
            history.insert(0, r)
            r = history.pop()
            r.history = history

        if not allow_redirects:
            try:
                r._next = next(self.resolve_redirects(r, request, yield_requests=True, **kwargs))
            except StopIteration:
                pass

        return r


class HttpRequest(requests.PreparedRequest, RandomUserAgentMixin, RequestMixin):

    def __init__(self):
        super().__init__()

    def reset_all(self):
        self.url = None
        self.headers = self.headers.clear() if self.headers else {}
        self.method = "GET"
        self.body = None
        self._cookies = self._cookies if self._cookies else None
        self.hooks = default_hooks()
        self._body_position = None
        return self

    def check(self):
        for attr in ("url", "method"):
            if not self.__getattribute__(attr):
                raise ValueError("The request must have `{}`".format(attr))

    def reset(self):
        self.url = None
        self.headers = None
        self.method = "GET"
        self.body = None
        self._body_position = None
        return self

    def add_hooks(self, hook_name: str, func):
        if not hasattr(func, "__call__"):
            logging.warning(f"{hook_name} has no `__call__` attribute `{hook_name}` will ignore")
            return self
        self.hooks[hook_name] = func
        return self


def dispatch(key, hooks, hook_data, **kwargs):
    hooks = hooks or {}

    def inner(_key, _hooks, _hook_data, **_kwargs):
        _hooks = _hooks.get(_key)
        if _hooks:
            if hasattr(_hooks, '__call__'):
                _hooks = [_hooks]
            for hook in _hooks:
                hook(_hook_data, **_kwargs)

    if isinstance(key, str):
        inner(key, hooks, hook_data, **kwargs)
    if isinstance(key, list):
        for k in key:
            inner(k, hooks, hook_data, **kwargs)
