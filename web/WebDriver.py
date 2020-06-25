import logging
import time
from typing import List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

from tools.date import DateTime
from tools.file import FileUtil
from web.FireFoxProfile import FireFoxProfile
from web.PageObject import PageObject


class Driver:
    __slots__ = [
        "__driver",
        "__firefox_profile",
        "executable_path",
        "use_color",
        "table",
        "enable_color"
    ]

    def __init__(self, kind="firefox", executable_path="", need_download_file=False, enable_color=True):
        """

        driver = Driver(kind="chrome",executable_path="xxx", enable_color=False)
        :param kind: 指定需要启动的浏览器类型
        :param executable_path: 指定浏览器驱动
        :param need_download_file: 指定是否需要启用下载配置(仅火狐浏览器)
        :param enable_color: 是否启用元素着色
        """
        self.__firefox_profile = None
        if need_download_file:
            self.__firefox_profile = self.init_fire_fox_profile()
        if executable_path == "":
            raise NotADirectoryError("请检查驱动路径和executable_path参数")
        self.executable_path = FileUtil.check_execute_able_path(executable_path)
        self.table = {
            "firefox": webdriver.Firefox,
            "chrome": webdriver.Chrome,
            "edge": webdriver.Edge,
            "ie": webdriver.Ie,
            "opera": webdriver.Opera,
            "phantomJS": webdriver.PhantomJS,
            "safari": webdriver.Safari,
            "remote": webdriver.Remote,
        }
        logging.info("正在初始化{}浏览器".format(kind))
        self.__driver = self.init(kind)
        logging.info("{}浏览器初始化成功".format(kind))
        self.use_color = False
        self.enable_color = enable_color

    @staticmethod
    def init_fire_fox_profile():
        return FireFoxProfile(). \
            close_download_interface(). \
            close_download_window(). \
            close_focus(). \
            close_info_alert_when_download_finish(). \
            set_browser_download_path(FireFoxProfile.DOWNLOAD_TO_DEFAULT_PATH). \
            make()

    def init(self, kind):
        """
        :param kind: 指定浏览器类型
        :return:
        """
        kind = kind.lower()
        try:
            dr = self.table[kind]
            if kind == 'firfox':
                return dr(executable_path=self.executable_path, firefox_profile=self.__firefox_profile)
            else:
                return dr(executable_path=self.executable_path)
        except KeyError:
            raise TypeError("不支持该浏览器:【{}】".format(kind))

    def find_po_element(self, args: tuple) -> WebElement:
        """
        例如：
            po = PageObject("./element.ini")
            po.set_section("login")
            driver.find_po_element(po.get_element('username'))
        :param args:
        :return:
        """
        method, value = args
        return self.find_element(PageObject.PoToBy[method], value)

    def find_element(self, method: str, value: str, timeout=10) -> WebElement:
        """
        带有智能等待的定位方法
        例如：
            driver.find_element("id","kw")
        :param method: 定位方式
        :param value: 定位值
        :param timeout: 最大超时时间，如果这个时间内没有找到该元素，将会抛出TimeOutException
        :return:
        """
        logging.debug("当前定位方式：【{}】，定位值：【{}】".format(method, value))
        if method.lower() == "js":
            return self.find_element_by_js_query_selector(value)
        if method.lower() == "java_script":
            return self.execute_java_script(value)
        ele = WebDriverWait(self.__driver, timeout). \
            until(EC.visibility_of_element_located((method, value)),
                  message="没有找到该元素 定位方式：【{}】,值为【{}】,请检查是否有新窗口跳出或者没有切换iframe".format(method, value))
        if isinstance(ele, WebElement):
            if self.enable_color:
                self.execute_element_with_color(ele)
            return ele
        raise NoSuchElementException(ele)

    def find_element_from_file(self, value: tuple) -> WebElement:
        method, v = value
        return self.find_element(method, v)

    def find_elements_from_file(self, value: tuple) -> List[WebElement]:
        method, v = value
        return self.find_elements(method, v)

    def find_element_by_id(self, value: str) -> WebElement:
        return self.find_element(By.ID, value)

    def find_element_by_name(self, value: str) -> WebElement:
        return self.find_element(By.NAME, value)

    def find_element_by_xpath(self, value: str) -> WebElement:
        return self.find_element(By.XPATH, value)

    def find_element_by_tag_name(self, value: str) -> WebElement:
        return self.find_element(By.TAG_NAME, value)

    def find_element_by_link_text(self, value: str) -> WebElement:
        return self.find_element(By.LINK_TEXT, value)

    def find_element_by_class_name(self, value: str) -> WebElement:
        return self.find_element(By.CLASS_NAME, value)

    def find_element_by_css_selector(self, value: str) -> WebElement:
        return self.find_element(By.CSS_SELECTOR, value)

    def find_element_by_partial_link_text(self, value: str) -> WebElement:
        return self.find_element(By.PARTIAL_LINK_TEXT, value)

    def find_element_by_js_query_selector(self, js: str) -> WebElement:
        e = self.__driver.execute_script('return document.querySelector("{}")'.format(js))
        if isinstance(e, WebElement):
            return e
        raise NoSuchElementException("根据表达式【{}】没有找到该元素".format(js))

    def find_elements(self, method: str, value: str, timeout=30) -> List[WebElement]:
        """
        带有智能等待的定位方法，多元素
        :param method: 定位方式
        :param value: 定位值
        :param timeout: 最大超时时间，如果这个时间内没有找到该元素，将会抛出TimeOutException
        :return:
        """
        logging.debug("当前定位方式：【{}】，定位值：【{}】".format(method, value))
        if method.lower() == 'js':
            return self.find_elements_by_js_query_selector(value)
        if method.lower() == "java_script":
            return self.execute_java_script(value)
        ele = WebDriverWait(self.__driver, timeout). \
            until(EC.visibility_of_all_elements_located((method, value)),
                  message="没有找到该元素 定位方式：【{}】,值为【{}】,请检查是否有新窗口跳出或者没有切换iframe".format(method, value))
        if isinstance(ele, list):
            return ele
        raise NoSuchElementException(ele)

    def find_elements_by_id(self, value: str) -> List[WebElement]:
        return self.find_elements(By.ID, value)

    def find_elements_by_name(self, value: str) -> List[WebElement]:
        return self.find_elements(By.NAME, value)

    def find_elements_by_xpath(self, value: str) -> List[WebElement]:
        return self.find_elements(By.XPATH, value)

    def find_elements_by_tag_name(self, value: str) -> List[WebElement]:
        return self.find_elements(By.TAG_NAME, value)

    def find_elements_by_link_text(self, value: str) -> List[WebElement]:
        return self.find_elements(By.LINK_TEXT, value)

    def find_elements_by_class_name(self, value: str) -> List[WebElement]:
        return self.find_elements(By.CLASS_NAME, value)

    def find_elements_by_css_selector(self, value: str) -> List[WebElement]:
        return self.find_elements(By.CSS_SELECTOR, value)

    def find_elements_by_partial_link_text(self, value: str) -> List[WebElement]:
        return self.find_elements(By.PARTIAL_LINK_TEXT, value)

    def find_elements_by_js_query_selector(self, js: str) -> List[WebElement]:
        e = self.__driver.execute_script('return document.querySelectorAll("{}")'.format(js))
        if isinstance(e, list):
            return e
        raise NoSuchElementException("根据表达式【{}】没有找到该元素".format(js))

    def title(self) -> str:
        """
        返回当前的网页标题
        :return:  None
        """
        return self.__driver.title

    def current_url(self) -> str:
        """
        获取当前URL
        :return: string
        """
        return self.__driver.current_url

    def switch_to_first_window(self) -> None:
        """
        切换到第一个窗口
        :return: None
        """
        self.__driver.switch_to.window(self.__driver.window_handles[0])

    def switch_to_last_window(self) -> None:
        """
        切换到最后一个窗口
        :return: None
        """
        self.__driver.switch_to.window(self.__driver.window_handles[len(self.__driver.window_handles) - 1])

    def accept_alter(self) -> None:
        self.__driver.switch_to.alert.accept()

    def cancel_alter(self) -> None:
        self.__driver.switch_to.alert.dismiss()

    def send_alter(self, data) -> None:
        self.__driver.switch_to.alert.send_keys(data)

    def switch_to_window_index(self, index: int) -> None:
        """
        根据索引切换窗口
        :param index: 索引位置
        :return: None
        """
        assert 0 < index < len(self.__driver.window_handles), "index out of bounds"
        self.__driver.switch_to.window(self.__driver.window_handles[index])

    def current_windows_handle(self) -> str:
        """
        获取当前窗口句柄
        :return: string
        """
        return self.__driver.current_window_handle

    def switch_to_parent_handle(self) -> None:
        """
        返回主frame
        :return: None
        """
        self.__driver.switch_to.default_content()

    def switch_to_iframe(self, method: str, value: str) -> None:
        """
        带有智能等待的切换iframe方法
        :param method: 定位方式
        :param value:  定位表达式
        :return: None
        """
        self.__driver.switch_to.frame(self.find_element(method, value))

    def switch_to_iframe_element(self, ele: WebElement) -> None:
        """
        切换iframe
        :param ele: iframe的name,索引,WebElement对象
        :return: None
        """
        self.__driver.switch_to.frame(ele)

    @property
    def driver(self) -> WebDriver:
        """
        获取原生WebDriver对象
        :return: WebDriver
        """
        return self.__driver

    def save_screen_shot(self) -> None:
        """
        根据日期时间创建文件夹并截图
        :return: None
        """
        filename = FileUtil.current_date_dir()
        current_time = DateTime.current_time() + ".png"
        filename = FileUtil.path_join(filename, current_time)
        self.__driver.save_screenshot(filename)

    def get(self, url) -> None:
        self.__driver.get(url)

    def __enter__(self):
        """
        会自动关闭浏览器
        with Driver() as driver:
            driver.find_element(...)
            ....
        :return:
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__driver.close()

    @staticmethod
    def stop(sec: int) -> None:
        """
        休眠
        :param sec: 休眠秒数
        :return: None
        """
        if sec < 0:
            sec = 0
        time.sleep(sec)

    def implicitly_wait(self, sec: int) -> None:
        """
        隐式等待
        :param sec: 秒数
        :return: None
        """
        self.__driver.implicitly_wait(sec)

    def scroll_to_up(self) -> None:
        """
        移动到最上边
        :return: None
        """
        self.__driver.execute_script("document.documentElement.scrollTop=scrollMaxX")

    def scroll_to_down(self) -> None:
        """
        移动到最下边
        :return: None
        """
        self.__driver.execute_script("document.documentElement.scrollTop=scrollMaxY")

    def scroll_to_right(self) -> None:
        """
        移动到最右边
        :return: None
        """
        self.__driver.execute_script("document.documentElement.scrollLeft=document.documentElement.scrollLeftMax")

    def scroll_to_left(self) -> None:
        """
        移动到最左边
        :return: None
        """
        self.__driver.execute_script("document.documentElement.scrollLeft=0")

    def scroll_to_position(self, x: int, y: int) -> None:
        """
        将滚动条滚动到指定坐标
        :param x: 要移动的x坐标
        :param y: 要移动的y坐标
        :return:None
        """
        self.__driver.execute_script("document.documentElement.scrollTo({0},{1}})".format(x, y))

    def scroll(self, start, end):
        """
        将滚动条滚动到指定坐标
        :param end:
        :param start:
        :return:None
        """
        self.__driver.execute_script("window.scrollTo({0},{1})".format(start, end))

    def scroll_to_element_by_id(self, ele_id: int) -> None:
        """
        将元素移动到可见区域
        :param ele_id: 元素id
        :return:None
        """
        self.__driver.execute_script('document.getElementById("{}").scrollIntoView(true)'.format(ele_id))

    def scroll_to_element(self, ele: WebElement) -> None:
        """
        将元素移动到可见区域
        :param ele:
        :return:None
        """
        self.__driver.execute_script('arguments[0].scrollIntoView(true)', ele)

    def get_element_functional(self, element: WebElement, functional: str) -> str:
        """
        获取元素属性
        :param element:  定位到的元素
        :param functional:  元素值
        :return: string,list,dict
        """
        return self.__driver.execute_script('return arguments[0].{}'.format(functional), element)

    def get_element_outer_html(self, element: WebElement) -> str:
        """
        获取元素外部的所有子标签
        :param element: 定位到的元素
        :return: string
        """
        return self.get_element_functional(element, "outerHTML")

    def remove_element(self, ele: WebElement) -> None:
        """
        移除定位到的元素
        :param ele:
        :return:
        """
        self.execute_java_script("arguments[0].outerHTML=''", ele)

    def get_element_inner_html(self, element: WebElement) -> str:
        """
        获取元素内部的所有子标签
        :param element: 定位到的元素
        :return: string
        """
        return self.get_element_functional(element, "innerHTML")

    def get_element_inner_text(self, element):
        """
        获取元素内部的文本值
        :param element: 定位到的元素
        :return: string
        """
        return self.get_element_functional(element, "innerText")

    def get_element_attributes(self, element: WebElement):
        """
        获取元素所有属性
        :param element: 定位的元素
        :return: dict
        """
        return self.get_element_functional(element, "attributes")

    def element_contains(self, element: WebElement, name=None, attrs=None, text=None):
        """
        元素是否包含符合条件的子标签
        :param element: 定位到的元素
        :param name: 子标签名
        :param attrs: 子标签属性值
        :param text: 子标签值
        :return: Bool
        """
        html = self.get_element_inner_html(element)
        bs = BeautifulSoup(html, features="lxml")
        res = bs.find_all(name=name, attrs=attrs, text=text)
        if res is None or len(res) == 0:
            return False
        return True

    @staticmethod
    def element_test_equal(element: WebElement, text: str) -> bool:
        """
        判断元素值是否相等
        :param element: 定位到的元素
        :param text:  判断的值
        :return: Bool
        """
        return element.text == text

    def set_element_attribute(self, element: WebElement, attr: str, value: str) -> None:
        """
        设置元素属性
        :param element:  定位到的元素
        :param attr:  属性名
        :param value:  属性值
        :return: None
        """
        self.__driver.execute_script("arguments[0].{0}={1}".format(attr, value), element)

    def set_element_value(self, element, value) -> None:
        """
        设置元素值
        :param element:
        :param value:
        :return: None
        """
        self.set_element_attribute(element, "value", value)

    def set_element_visible(self, locator) -> None:
        """
        设置元素可见
        使用css定位方式
        :param locator: css表达式
        :return:
        """
        js = 'document.querySelector("{}")'.format(locator)
        style_visibility = self.__driver.execute_script('return {}.style.visibility'.format(js))
        style_display = self.__driver.execute_script('return {}.style.display'.format(js))
        type_hidden = self.__driver.execute_script('return {}.type'.format(js))
        if style_visibility != "visible":
            self.__driver.execute_script('{}.style.visibility="visible"'.format(js))
        if style_display != "block":
            self.__driver.execute_script('{}.style.display="block"'.format(js))
        if type_hidden == "hidden":
            self.__driver.execute_script('{}.type="visible"'.format(js))

    def execute_element_with_color(self, element) -> None:
        """
        执行元素时高亮显示
        :param element: 要执行的元素
        :return: None
        """
        self.__driver.execute_script("arguments[0].setAttribute('style',arguments[1])", element,
                                     'border:2px solid red;')

    def close(self) -> None:
        logging.info("正在关闭浏览器")
        self.__driver.close()

    def floating_box_with_element(self, attr, value, index) -> WebElement:
        """
        选择浮动框中的值
        :param attr:  浮动框ul的属性
        :param value:  属性值
        :param index:  索引位置
        :return: WebElement
        """
        return self.find_element_by_xpath("//ul[@{}='{}']//li[{}]".format(attr, value, index))
        # action = ActionChains(driver=self.__driver)
        # for i in range(index):
        #     action.key_down(Keys.DOWN).key_up(Keys.DOWN).perform()
        # action.key_down(Keys.ENTER).key_up(Keys.ENTER).perform()

    def set_current_time_po(self, args) -> None:
        m, v = args
        return self.set_current_time(PageObject.PoToBy[m], v)

    def set_current_time(self, method, value) -> None:
        """
        设置当前时间到时间输入框
        :param method:  定位方式
        :param value: 定位值
        :return:WebElement
        """
        return self.set_current_time_use_element(self.find_element(method, value))

    @staticmethod
    def set_current_time_use_element(element: WebElement) -> None:
        """
        设置当前时间到时间输入框
        :param element: 时间输入框对象
        :return: WebElement
        """
        return element.send_keys(DateTime.current_date_time())

    def select_po(self, args: tuple) -> Select:
        method, value = args
        return self.select(PageObject.PoToBy[method], value)

    def select(self, method: str, value: str) -> Select:
        """
        处理选择框
        :param method: 定位方式
        :param value:  定位值
        :return:Select
        """

        ele = self.find_element(method, value)
        return self.select_use_element(ele)

    @staticmethod
    def select_use_element(element: WebElement) -> Select:
        """
        处理选择框
        :param element: 定位的元素
        :return: Select
        """
        return Select(element)

    def execute_java_script(self, js, *args):
        return self.__driver.execute_script(js, *args)

    def element_action_with_locator(self, method: str, value: str) -> ActionChains:
        """
        根据定位方式获取动作
        :param method:
        :param value:
        :return:
        """
        if method == "js":
            ele = self.find_element_by_js_query_selector(value)
        else:
            ele = self.find_element(method, value)
        return self.element_action(ele)

    @staticmethod
    def element_action(element: WebElement) -> ActionChains:
        return ActionChains(element)

    def new_window_and_switch(self) -> None:
        """
        打开一个新的窗口并切换到该窗口（默认切换到最后一个）如果在中天弹出需要用new_window
        :return:
        """
        self.__driver.execute_script("window.open('')")
        self.switch_to_last_window()

    def new_window(self, url: str) -> None:
        """
        打开一个新的窗口
        :param url:
        :return:
        """
        self.__driver.execute_script('window.open("arguments[0]")', url)
