"""

c = Clinet()
res = c.do(xx).result()
convey = Convey(self)

So(res.headers,should_be_equal,{"xx"})
So(res,should_not_none)
So(res.text,should_not_none)
So(res,status_code,should_be_equal,200)
"""
import logging
import re
import unittest

from httpclient.funcions import should_not_none


class ResponseTable:
    Headers = "headers"  # HTTP响应头部
    Text = "text"  # HTTP响应文本
    StatusCode = "status_code"  # HTTP响应状态吗
    Url = "url"  # HTTP响应URL
    IsRedirect = "is_redirect"  # HTTP是否被重定向
    History = "history"  # http历史URL


class HttpStatus:
    SwitchingProtocols = 101
    Processing = 102
    Checkpoint = 103
    UriTooLong = 122
    Ok = 200
    Created = 201
    Accepted = 202
    NonAuthoritativeInfo = 203
    NoContent = 204
    ResetContent = 205
    PartialContent = 206
    MultiStatus = 207
    AlreadyReported = 208
    ImUsed = 226
    MultipleChoices = 300
    MovedPermanently = 301
    Found = 302
    SeeOther = 303
    NotModified = 304
    UseProxy = 305
    SwitchProxy = 306
    TemporaryRedirect = 307
    PermanentRedirect = 308
    BadRequest = 400
    Unauthorized = 401
    PaymentRequired = 402
    Forbidden = 403
    NotFound = 404
    MethodNotAllowed = 405
    NotAcceptable = 406
    ProxyAuthenticationRequired = 407
    RequestTimeout = 408
    Conflict = 409
    Gone = 410
    LengthRequired = 411
    PreconditionFailed = 412
    RequestEntityTooLarge = 413
    RequestUriTooLarge = 414
    UnsupportedMediaType = 415
    RequestedRangeNotSatisfiable = 416
    ExpectationFailed = 417
    ImATeapot = 418
    MisdirectedRequest = 421
    UnprocessableEntity = 422
    Locked = 423
    FailedDependency = 424
    UnorderedCollection = 425
    UpgradeRequired = 426
    PreconditionRequired = 428
    TooManyRequests = 429
    HeaderFieldsTooLarge = 431
    NoResponse = 444
    RetryWith = 449
    BlockedByWindowsParentalControls = 450
    UnavailableForLegalReasons = 451
    ClientClosedRequest = 499
    InternalServerError = 500
    NotImplemented = 501
    BadGateway = 502
    ServiceUnavailable = 503
    GatewayTimeout = 504
    HttpVersionNotSupported = 505
    VariantAlsoNegotiates = 506
    InsufficientStorage = 507
    BandwidthLimitExceeded = 509
    NotExtended = 510
    NetworkAuthenticationRequired = 511


class JsonConveyMixin:
    __slots__ = ()

    def so_json_item(self, except_item, fn, except_value=None):
        """
        断言json中某个key value值（value值不为json或array）
        例如：
            {
                "name": "admin",
                "list": ["1","2","3"],
                "dict": {
                    "age":18,
                    "phone":"123456789",
                    "li":[1,2,3,4]
                    },
            }

        so_json_item("name", should_equal, "admin")

        :param except_item: json的key
        :param fn: 断言函数
        :param except_value: json的期待的值
        :return:
        """
        if hasattr(self, "js"):
            return self.so(self.js.item(except_item).value, fn, except_value)
        raise ValueError("返回结果不是json或者没有调用except_json方法")

    def so_json_array(self, except_item, fn, except_value=None):
        """
        断言json中某个key value值（value必须是array）
        例如：
            {
                "name": "admin",
                "list": ["1","2","3"],
                "dict": {
                    "age":18,
                    "phone":"123456789",
                    "li":[1,2,3,4]
                    },
            }

        so_json_array("list",should_equal, ["1","2","3"])
        :param except_value:
        :param except_item:
        :param fn:
        :return:
        """
        if hasattr(self, "js"):
            return self.so(self.js.array(except_item).value, fn, except_value)
        raise ValueError("返回结果不是json或者没有调用except_json方法")

    def so_json_array_index(self, except_item, except_index: int, fn, except_value=None):
        """
        断言json中某个key value值（value必须是array的索引位置）
        例如：
            {
                "name": "admin",
                "list": ["1","2","3"],
                "dict": {
                    "age":18,
                    "phone":"123456789",
                    "li":[1,2,3,4]
                    },
            }
        so_json_array_index("list", 0 ,should_equal,"1")
        :param except_item: 期望数组的键
        :param except_index: 期望数组的索引
        :param fn:
        :param except_value: 期待的值
        :return:
        """

        if hasattr(self, "js"):
            self.so(self.js.array(except_item).index(except_index).value, fn, except_value)
        raise ValueError("返回结果不是json或者没有调用except_json方法")

    def so_json_items(self, except_item, fn, except_value=None):
        """
        断言json中某个key value值（value必须是json对象）
        例如：
            {
                "name": "admin",
                "list": ["1","2","3"],
                "dict": {
                    "age":18,
                    "phone":"123456789",
                    "li":[1,2,3,4]
                    },
            }
        so_json_items("dict",should_equal, {
            "age":18,
            "phone":"123456789",
            "li":[1,2,3,4]
        })
        :param except_item:
        :param fn:
        :param except_value:
        :return:
        """
        if hasattr(self, "js"):
            self.so(self.js.items(except_item).value, fn, except_value)
        raise ValueError("返回结果不是json或者没有调用except_json方法")


class HttpConveyMixin:

    def regex(self, reg, index=0, trim=False):
        """
        使用正则表达式提取响应结果
        :param trim:
        :param reg: 表达式
        :param index: 获取第index个结果
        :return:
        """
        data = self.response.text
        if trim:
            data = data.replace("\n", "")
        try:
            return re.findall(reg, data)[index]
        except IndexError:
            logging.error("{}，内容没有提取到".format(reg))

    def so_body_text(self, fn, except_value):
        """
        断言响应体内容

        例如：
            so_body(should_contains,"admin")
        :param except_value: 预期结果
        :param fn: 断言函数
        :return:
        """
        return self.so_response("text", fn, except_value)

    def so_extract_body(self, except_value, fn, reg_func):
        """
         使用自定义提取函数,断言HTTP响应Body内容

        def check_response(data):
            return re.findall(".*user=(.+?)&pass=?",x)[0]

        so_extract_body("username", check_response)

        :param except_value: 预期结果
        :param fn: 断言函数
        :param reg_func: 提取式函数名
        :return:
        """
        return self.so(except_value, fn, self.response.extract(reg_func))

    def so_has_header(self, header_name):
        """
        断言HTTP响应响应头信息
        :param header_name:
        :return:
        """
        self.so(self.response.headers.get(header_name), should_not_none)

    def so_header(self, header_name, fn, header_value):
        """
        断言HTTP响应头部信息

        例如：
            响应头部信息
                {
                    ....
                    "Set-Cookie":"afsadfasdfsagsadg"
                }

        so_header("Set-Cookie",should_equal,"afsadfasdfsagsadg")

        :param header_name: 预期响应头字段
        :param fn: 断言函数
        :param header_value: 实际响应头字段内容
        :return:
        """
        self.so(self.response.headers[header_name], fn, header_value)

    def so_cookie(self, cookie_name, fn, cookie_value):
        """
        断言HTTP响应Cookie信息

        :param cookie_name: 预期响应头字段
        :param fn: 断言函数
        :param cookie_value: 实际Cookie值
        :return:
        """
        self.so(self.response.cookies[cookie_name], fn, cookie_value)

    def so_has_cookie(self, cookie_name):
        """
        断言HTTP响应Cookie信息
        :param cookie_name:
        :return:
        """
        self.so(self.response.cookies.get(cookie_name), should_not_none)

    def so_status_code(self, fn, except_value):
        """
        断言HTTP状态码信息
        :param fn:
        :param except_value:
        :return:
        """
        self.so_response("status_code", fn, except_value)

    def so_response(self, where, fn, except_value):
        """
        只使用HTTP请求结果

        ex = self.client.do("http://192.168.1.24/DBShop/user/register").with_param(
            TestCases.man.get("succeed")).Except(self)

        ex.so_response(ResponseTable.Text, should_contains, "adminsbaaaa")

        :param where:  指定要断言Response内容 使用ResponseTable指定
        :param fn: 断言函数
        :param except_value: 预期结果
        :return:
        """
        return self.so(getattr(self.response, where), fn, except_value)

    @property
    def except_json(self):
        """
        提取响应结果，并转为json形式
        :return:
        """
        setattr(self, "js", self.response.json)
        return self

    def set_response(self, resp):
        setattr(self, "response", resp)
        return self


class Convey(JsonConveyMixin, HttpConveyMixin):
    __test: unittest.TestCase

    def __init__(self, case):
        self.__test = case

    def so(self, except_value, fn, real_value=None):
        """
        def add(a,b):
            return a + b

        res = add(1,2)
        so(res, should_equal, 3)

        :param except_value: 预期结果
        :param fn: 断言函数
        :param real_value: 实际结果
        :return:
        """
        return fn(self.__test, except_value, real_value)

    @property
    def result(self):
        """
        返回响应结果
        :return:
        """
        return self.response
