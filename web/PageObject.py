import re
from configparser import ConfigParser

from selenium.webdriver.common.by import By


class PageObject:
    __slots__ = [
        "config",
        "current_section"
    ]

    PoToBy = {
        "id": By.ID,
        "xpath": By.XPATH,
        "p_link_text": By.PARTIAL_LINK_TEXT,
        "link_text": By.LINK_TEXT,
        "tag_name": By.TAG_NAME,
        "css": By.CSS_SELECTOR,
        "class_name": By.CLASS_NAME,
        "name": By.NAME,
        "js": "js",
        "jsc": "java_script"
    }

    def __init__(self, filename):
        self.config = ConfigParser()
        self.config.read(filename)
        self.current_section = ""

    def set_current_section(self, section: str):
        self.current_section = section

    def get_element(self, name: str):
        """
        例如：
            [login]
            # 元素类型_元素名
            input_username= (id,user_name)
        set_current_section("login")
        get_element("input_username") -> (id,user_name)
        :param name:
        :return:
        """
        # 获取时设置当前的域
        if self.current_section == "":
            raise ValueError("请设置当前的section")
        # 获取值
        result = self.config.get(self.current_section, name)
        # 利用正则表达式解析处值  （id,user_name）
        parser_result = re.findall(r"\((\w{2,10}),(.+)\)", result)
        if len(parser_result) == 0:
            raise SyntaxError("{}:语法错误".format(result))
        try:
            # method = id , value=user_name  （id,user_name）
            method, value = parser_result[0]
            # 将获取的method进行转换成合法的定位值(By中的)
            return PageObject.PoToBy[method], value
        except KeyError:
            raise SyntaxError("元素定位语法错误，必须是以下值:{}".format(",".join([x for x in PageObject.PoToBy])))
        except IndexError:
            raise SyntaxError("{}:语法错误".format(parser_result[0]))
