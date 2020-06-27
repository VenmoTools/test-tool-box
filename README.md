# test-tool-box
为测试提供基本工具库

# 目录结构

[app](app): 该模块封装了`adb`常用的命令和对appium的二次封装

[httpclient](httpclient): 该模块重新编写了requests库的Response，Request，HttpClient模块 ，提供了断言功能

[report](report)： 该模块引用了`HTMLTestReportCN`用于生成测试报告

[net](net): 
    + [emailsender.py](net/emailsender.py) 提供了 Email的构建，支持SMTP协议，支持TLS和用户认证
    + [tcp.py](net/tcp.py) 提供了简易的tcp服务器和tcp客户端
    + [ssl_tcp.py](net/ssl_tcp.py) 提供了TLS版本的TCP服务器和客户端

[tools](tools): 
    + [data.py](tools/date.py): 提供了日期时间操作
    + [encryption.py](tools/encryption.py): 提供了url转码解码，md5加密，base64加密解密，RSA加密，DES，AES加密（待完善）等
    + [file.py](tools/file.py): 提供了文件目录相关操作
    + [math.py](tools/math.py): 提供了存储单位，时间单位的单位转换功能

[web](web): 对selenium二次封装提供了扩展功能例如窗口滚动，元素自动高亮显示，浏览器窗口操作等功能支持PO模型可通过.ini文件来完成


# 工具的内容
工具库主要包含以下内容：

## 接口测试
重写requests Request和Response内容提供了测试常用的功能例如

### 响应断言
HttpClient自带响应断言方式这利用unittest库的函数，例如
```python
import re
import unittest

from httpclient.HttpClient import HttpClient
from httpclient.funcions import should_equal, should_not_equal


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.client = HttpClient()

    def test_response(self):
        ex = self.client.do("http://cn.bing.com").http_except(self)
        ex.so_body_text(should_equal, "abc")
        ex.so_has_header("Host")  # 断言响应头应该包含Host
        ex.so_header("Host", should_not_equal, "www.example.com")  # 断言响应头应该Host字段值为www.example.com
        ex.so_has_cookie("PHPSESSION")  # 断言响应头应该包含名为PHPSESSION的Cookie
        # 断言响应头应该名为PHPSESSION的Cookie字段值为ototlqt0uuhr2ejhrnlfqv6fsq
        ex.so_cookie("PHPSESSION", should_not_equal, "ototlqt0uuhr2ejhrnlfqv6fsq")
        ex.so_status_code(should_equal, 200)  # 断言响应码为200
        # 利用正则表达式提取响应体的内容应该为 admin
        ex.so_extract_body(lambda data: re.findall(".*user=(.+?)&pass=?", data)[0], should_equal, "admin")
        ex.so(ex.regex(".*user=(.+?)&pass=?", 0), should_equal, "admin")

    def test_json(self):
        """
        响应结果为
        {
                "name": "admin",
                "list": ["1","2","3"],
                "dict": {
                    "age":18,
                    "phone":"123456789",
                    "li":[1,2,3,4]
                    },
        }
        """
        ex = self.client.do("http://cn.bing.com").http_except(self).except_json
        ex.so_json_item("name", should_equal, "admin")
        ex.so_json_array("list", should_equal, ["1", "2", "3"])
        ex.so_json_items("dict", should_equal, {
            "age": 18,
            "phone": "123456789",
            "li": [1, 2, 3, 4]
        })
        ex.so_json_array_index("list", 0, should_equal, "1")


if __name__ == '__main__':
    unittest.main()

```
如果我不想用unittest库怎么把？

没关系，您只需要重新定义`httpclient.functions`模块中的所有函数即可，该模块中的函数都是回调函数，它通过http_except传递测试框架的实例来完成的

例如`should_equal`函数
```python
def should_equal(test, except_value, real_value):
    return test.assertEqual(except_value, real_value)
```
`test`为测试框架的实例，您可以在这里调用框架的断言函数


### 函数装饰器
简化请求过程
```python
from httpclient.HttpClient import HttpClient 

client = HttpClient()

@client.do_request(url="http://www.baidu.com", method="GET")
def handler(response):
    print(response.text)


if __name__ == '__main__':
    handler()
``` 

### 随机User-Agent
通过调用`enable_random_ua`方法来启动随机User-Agent，也可以通过`disable_random_ua`方法来关闭

```python
from httpclient.HttpClient import HttpClient 

client = HttpClient()
client.enable_random_ua()
res = client.do("http://cn.bing.com").result
print(res.request.headers)
```
> 注意： 启用随机UA时会强制删除Header中的User-Agent

### 回调函数
回调函数通过`add_hooks`方法注册，注册后并不会直接调用，需要调用`dispatch_hooks`方法指定需要哪些回调函数需要执行,
request内置了名为`response`的hook，因此在注册时不要将hook的name设置为`response`

```python
from httpclient.HttpClient import HttpClient

def print_header(response, **kwargs):
    print(response.request.headers)
    return response

def print_response(response, **kwargs):
    print(response.text)
    return response

if __name__ == '__main__':
    client = HttpClient()
    client.enable_random_ua()
    client.add_hooks("header", print_header)
    client.add_hooks("resp", print_header)
    client.dispatch_hooks("test")
    res = client.do("http://cn.bing.com").result
```

通过`add_hooks`注册的回调函数不要修改响应结果，如果需要通过回调函数修改请使用`response_hook`修改

```python
from httpclient.HttpClient import HttpClient

def callback(response, **_kwargs):
    response.request.headers["Host"] = "abc"
    return response


if __name__ == '__main__':
    client = HttpClient()
    client.enable_random_ua()
    client.response_hooks(callback)
    res = client.do("http://cn.bing.com").result
    print(res.request.headers)
```

### 添加Header

可以使用`with_headers`来添加请求头

```python
from httpclient.HttpClient import HttpClient

if __name__ == '__main__':
    client = HttpClient()
    header = {
                 "PHPSESSID": "ototlqt0uuhr2ejhrnlfqv6fsq",
                 "Accept":"text/html,application/xhtml+xml,*/*;q=0.8"
             }
    res = client.do("http://cn.bing.com").with_headers(header).result
    print(res.request.headers)
```

在测试过程中经常需要通过测试用例来读取请求头数据，测试用例往往会写在excel中，因此可以使用下列方式请求完成

#### 使用文本形式的Header
语法格式为:

`Header键(Header值)`  如果有多个Header值使用`|`分割

例如：
```
Cookie(PHPSESSID=ototlqt0uuhr2ejhrnlfqv6fsq)|Accept(text/html,application/xhtml+xml,*/*;q=0.8)
表示
{
    "PHPSESSID": "ototlqt0uuhr2ejhrnlfqv6fsq",
    "Accept":"text/html,application/xhtml+xml,*/*;q=0.8"
}
```

```python
from httpclient.HttpClient import HttpClient

if __name__ == '__main__':
    client = HttpClient()
    header = "Cookie(PHPSESSID=ototlqt0uuhr2ejhrnlfqv6fsq)|Accept(text/html,application/xhtml+xml,*/*;q=0.8)"
    res = client.do("http://cn.bing.com").with_text_header(header).result
    print(res.request.headers)
```

### 查询参数

查询参数一般用于`GET`请求中，通过`do_with_query`方法来完成该操作

使用带有查询的url
例如：
    `http://192.168.1.24/page?p=15&index=12`
请求：
#### 文本形式
```python
from httpclient.HttpClient import HttpClient

if __name__ == '__main__':
    client = HttpClient()
    res = client.do_with_query(" http://192.168.1.24/page","p=15&index=12").result
    print(res.text)
```
#### 字典形式
```python
from httpclient.HttpClient import HttpClient

if __name__ == '__main__':
    param = {
        "p":15,
        "index":12,
    }
    client = HttpClient()
    res = client.do_with_query(" http://192.168.1.24/page",param).result
    print(res.text)
```

### 请求体
#### POST表单请求体
使用字符串的形式传递参数

```python
from httpclient.HttpClient import HttpClient

if __name__ == '__main__':
    client = HttpClient()
    res = client.do("http://192.168.1.24/login")\
        .with_method("POST")\
        .with_text_param("user=admin&password=123456")\
        .result
    # 或者使用更简单的 with_post_text("user=admin&password=123456")
    print(res.text)
```


#### POST with json

```python
from httpclient.HttpClient import HttpClient

if __name__ == '__main__':
    param = {
        "p":15,
        "index":12,
    }
    client = HttpClient()
    res = client.do("http://192.168.1.24/login")\
        .with_method("POST")\
        .with_json(param)\
        .result
    # 或者使用更简单的 with_post_json(param)
    print(res.text)
```

#### POST with file

```python
from httpclient.HttpClient import HttpClient

if __name__ == '__main__':
    client = HttpClient()
    res = client.do("http://192.168.1.24/login")\
        .with_method("POST")\
        .with_file("example.txt")\
        .result
    print(res.text)
```


#### 自定义POST请求体
如果需要以上API不能够满足你，你可以使用`with_post_body`来自定义想要传递的内容

```python
from httpclient.HttpClient import HttpClient

if __name__ == '__main__':
    param = {
        "p":15,
        "index":12,
    }
    client = HttpClient()
    res = client.do("http://192.168.1.24/login")\
        .with_post_body(json=param)\ 
        .result 
    print(res.text)
```

