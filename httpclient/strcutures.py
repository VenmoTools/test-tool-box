import json
import logging
import pickle
import re

import chardet
import faker
from urllib3.exceptions import InvalidHeader

_COOKIE_PARSER = re.compile(r"([\w\-\d]+)\((.*)\)")
_CLEAN_HEADER_REGEX_BYTE = re.compile(b'^\\S[^\\r\\n]*$|^$')
_CLEAN_HEADER_REGEX_STR = re.compile(r'^\S[^\r\n]*$|^$')
_HOST_EXTRACT = h = re.compile(r'https?://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}[:\d]{1,6}|[\w\d.\-]?[\w\d.\-]+)/?')
_DECODE_PARSER = re.compile(r"([\w\d\-]+)=([\w\d\-@.+]*)")


class JSON:
    __slots__ = [
        "__d",
        "__current"
    ]

    def __init__(self, t):
        self.__d = t
        self.__current = None

    """
    {
        "name": "admin",
        "list": ["1","2","3"],
        "dict": {
            "age":18,
            "phone":"123456789",
            "li":[1,2,3,4]
        },
    }
    JSON(xxx).Item("name").Value()  ->  admin
    JSON(xxx).Array("list").Index(0).Value() -> 1
    JSON(xxx).Items("dict").Item("age").Value() -> 18
    JSON(xxx).Items("dict").Array("li").Index(0) -> 1
    """

    def item(self, data):
        if self.__current:
            self.__current = self.__current[data]
        else:
            self.__current = self.__d[data]
        return self

    def restart(self):
        self.__current = None
        return self

    def array(self, key):
        if self.__current:
            self.__current = self.__current[key]
        else:
            self.__current = self.__d[key]
        return self

    def index(self, index):
        if isinstance(self.__current, list):
            self.__current = self.__current[index]
            return self
        raise TypeError("except list but given {} ".format(self.__current.__class__))

    @property
    def value(self):
        data = self.__current

        if self.__current:
            self.restart()
            return data
        return self.__d

    def items(self, key):
        if self.__current:
            self.__current = self.__current[key]
        else:
            self.__current = self.__d[key]
        return self

    @staticmethod
    def Except(case, except_value, fn, real_value):
        return fn(case, except_value, real_value)

    def __str__(self):
        return "{}".format(self.__d)


class RandomUserAgentMixin(object):
    __slots__ = ()

    def random(self):
        f = faker.Faker()
        yield f.user_agent()

    def enable_random_ua(self):
        setattr(self, "ua", True)
        return self

    def close_random_ua(self):
        if hasattr(self, "ua"):
            delattr(self, "ua")
        return self


class RequestMixin(object):
    __slots__ = ()

    def ready(self, method=None, url=None, headers=None, files=None, data=None,
              params=None, auth=None, cookies=None, hooks=None, json=None):
        if hasattr(self, "random") and hasattr(self, "ua") and self.ua:
            if headers:
                headers.update({"User-Agent": next(self.random())})
            else:
                headers = {"User-Agent": next(self.random())}
        self.prepare_method(method)
        self.prepare_url(url, params)
        self.prepare_headers(headers)
        self.prepare_cookies(cookies)
        self.prepare_body(data, files, json)
        self.prepare_auth(auth, url)
        self.prepare_hooks(hooks)
        return self

    @staticmethod
    def first_word_upper(key):
        first_char = key[:1]
        return first_char.upper() + key[1:]

    def __parser(self, item: str) -> tuple:
        try:
            key, value = _COOKIE_PARSER.findall(item)[0]
        except IndexError:
            raise SyntaxError("Header语法错误")

        if "_" in key:
            words = key.split("_")
            all_words = [self.first_word_upper(w) for w in words]
            key = "-".join(all_words)

        return key, value

    def parser(self, line: str):
        """
        Line的格式
            字段名(字段值)
            如果有多个字段以|分割
        例如
            Cookie(PHPSESSID=ototlqt0uuhr2ejhrnlfqv6fsq)|Accept(text/html,application/xhtml+xml,*/*;q=0.8)
        转换以后：
            {
                'Cookie': 'PHPSESSID=ototlqt0uuhr2ejhrnlfqv6fsq',
                'UserAgent': 'xxx', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
        :param line:
        """
        if "|" in line:
            for item in line.split("|"):
                header = self.__parser(item)
                check_header_validity(header)
                k, v = header
                self.headers[k] = v
        else:
            self.headers.update(self.__parser(line))


class ResponseMixin:
    __slots__ = ()

    def get_type(self):
        """
        获取响应内容的类型
        :return:
        """
        types = self.headers["Content-Type"]
        if types == "":
            raise TypeError("Content-Type没有数据")
        return types.split(";")[0]

    @property
    def charset(self):
        """
        返回响应结果的编码类型
        :return:
        """
        return chardet.detect(self.content)["encoding"]

    def regex(self, pattern: str, index=0, trim=False):
        """
        使用正则表达式提取响应体中的内容
        :param trim:
        :param pattern:
        :param index:
        :return:
        """
        data = self.text
        if trim:
            data = data.replace("\n", "")
        try:
            return re.findall(pattern, data)[index]
        except IndexError:
            logging.error("{}，内容没有提取到".format(pattern))

    def extract(self, fn):
        """
        执行响应体提取函数
        :param fn:
        :return:
        """
        return fn(self.text)

    @property
    def jsonify(self):
        """
        将响应结果转为Json对象
        该JSON对象可以提取内容，具体查看JSON类
        :return:
        """
        if self.content:
            if self.get_type() == "application/json":
                return JSON(json.loads(self.content, encoding=self.charset))
            try:
                return JSON(json.loads(self.content, encoding=self.charset))
            except json.JSONDecodeError:
                raise ValueError("返回内容不是json")
        return JSON({})

    def get_host(self):
        """
        获取响应主机名
        :return:
        """
        return _HOST_EXTRACT.findall(self.url)[0]

    def dump(self):
        """
        保存Response对象
        :return:
        """
        with open(self.get_host() + ".kpl", "wb") as f:
            pickle.dump(self, f)

    def dump_text_context(self):
        """
        将文本响应结果保存为文件形式
        文件名为主机名
        :return:
        """
        with open(self.get_host(), "w") as f:
            f.write(self.text)

    def dump_binary_context(self):
        """
        将二进制响应结果保存为文件形式
        文件名为主机名
        :return:
        """
        with open(self.get_host(), "wb") as f:
            f.write(self.content)


def check_header_validity(header):
    name, value = header

    if isinstance(value, bytes):
        pat = _CLEAN_HEADER_REGEX_BYTE
    else:
        pat = _CLEAN_HEADER_REGEX_STR
    try:
        if not pat.match(value):
            raise InvalidHeader("Invalid return character or leading space in header: %s" % name)
    except TypeError:
        raise InvalidHeader("Value for header {%s: %s} must be of type str or "
                            "bytes, not %s" % (name, value, type(value)))


def dict2text(data: dict):
    # dict -> admin=123&xx=222
    return "&".join(["{0}={1}".format(k, v) for k, v in data.items()])


def text2dict(data):
    # admin=123&xx=222 -> dict
    return {p[0]: p[1] for p in _DECODE_PARSER.findall(data)}


def WithContext(cls):
    __enter__ = cls.__enter__
    __exit__ = cls.__exit__

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.error("Excetions:\ntype:{0}\n\tvalue:{1}\n\ttrack back:{2}\n".format(exc_type, exc_val, exc_tb))
        if hasattr(self, "close"):
            self.close()

    cls.__enter__ = __enter__
    cls.__exit__ = __exit__

    return cls


class NoEnableCacheRequest(Exception):
    pass
