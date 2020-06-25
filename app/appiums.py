import requests
from appium import webdriver
from appium.webdriver.extensions.android.power import Power
from appium.webdriver.webdriver import WebDriver
from httpclient.Client import Response

from app.key_event import KeyEvent
from common.exceptions import ConfigError
from tools.date import DateTime
from tools.string import String

"""
1. 安装Java环境，Android，SDK
2. 配置Java环境变量（变量名JAVA_HOME），配置Android环境变量(ANDROID_HOME)
3. 如果是模拟器需要将模拟器的ADB.exe AdbWinApi.dll AdbWinUsbApi.dll拷贝到 sdk/platform-tools（记得备份里面的内容）
4. 安装Appium-Desktop，设置地址0.0.0.0 监听端口 4723
5. NewSession Custom-Server 地址主机IP，监听端口 4723
"""


class Config:

    def __init__(self):
        self.device_name = ""
        self.platform_version = ""
        self.platform_name = "Android"
        self.app_package = ""
        self.app_activity = ""
        self.no_reset = False

    def check_self(self):
        for k, v in self.__dict__.items():
            if isinstance(v, str) and v == "":
                raise ConfigError("{}没有配置或配置错误".format(k))

    @staticmethod
    def hungary_named(name: str):
        string = []
        for char in name:
            # platformVersion -> platform_version
            if char.isupper():
                string.append("_")
                char = char.lower()
            string.append(char)
        return "".join(string)

    @staticmethod
    def hump_name(name: str):
        res = name.split("_")
        first_word = res[0]
        res = res[1:]
        words = [String.first_word_upper(word) for word in res]
        words.insert(0, first_word)
        return "".join(words)

    def from_dict(self, d: dict):
        for k, v in d.items():
            # platformVersion -> platform_version
            self.__dict__[self.hungary_named(k)] = v

    def to_dict(self):
        return {self.hump_name(k): v for k, v in self.__dict__.items()}

    def set_device_name(self, name):
        self.device_name = name
        return self

    def set_platform_version(self, version):
        self.platform_version = version
        return self

    def set__platform_name(self, name):
        self.platform_name = name
        return self

    def set_app_package(self, app):
        self.app_package = app
        return self

    def set_app_activity(self, act):
        self.app_activity = act
        return self

    def set_no_reset(self, s):
        self.no_reset = s


class Information:

    def __init__(self):
        self.current_server = ""
        self.current_device = ""
        self.current_app_package = ""
        self.current_app_activity = ""
        self.current_device_power = ""
        self.current_ac_power = Power.AC_ON


class AppDriver:
    __driver: WebDriver
    __config: Config

    def __init__(self):
        self.__driver = None
        self.__config = None
        self.__current_server = ""
        self.__info = Information()

    def config(self, conf: Config):
        conf.check_self()
        self.__config = conf

    def config_from_dict(self, conf: dict):
        self.__config = Config()
        self.__config.from_dict(conf)
        self.__config.check_self()

    def server(self, url):
        self.__current_server = url

    @property
    def info(self):
        return self.__info

    def start(self):
        self.__driver = webdriver.Remote(command_executor=self.__current_server,
                                         desired_capabilities=self.__config.to_dict())
        self.__info.current_app_package = self.__config.app_package
        self.__info.current_app_activity = self.__config.app_activity
        self.__info.current_device = self.__config.device_name
        self.__info.current_server = self.__current_server

    def server_status(self) -> bool:
        res = Response(requests.get(self.__current_server + "/status")).jsonify()["status"]
        return res == 0

    def web_context_go_back(self):
        self.__driver.back()

    def take_screenshot(self):
        self.__driver.get_screenshot_as_file(DateTime.current_date_time())

    @property
    def driver(self):
        return self.__driver

    def close_ac_power(self):
        self.__driver.set_power_ac(Power.AC_OFF)

    def open_ac_power(self):
        self.__driver.set_power_ac(Power.AC_ON)

    def pull_file(self, file):
        self.__driver.pull_file(file)

    def pull_folder(self, file):
        """
        :param file:
        :return:
        """
        self.__driver.pull_folder(file)

    def press_home_button(self):
        """
        按下HOME键
        :return:
        """
        self.__driver.keyevent(KeyEvent.KEYCODE_HOME)

    def key_bord_shown(self):
        """
        判断虚拟键盘是否弹出
        :return:
        """
        return self.__driver.is_keyboard_shown()

    def close_key_bord(self):
        """
        关闭虚拟键盘
        :return:
        """
        self.driver.hide_keyboard()

    def close_key_bord_if_shown(self):
        """
        如果弹出虚拟键盘则关闭
        :return:
        """
        if self.key_bord_shown():
            self.close_key_bord()

    def set_net_work_speed(self, speed):
        """
        设置网速显示：用于测试弱网环境
        NetSpeed
        GSM = 'gsm'         # GSM/CSD (up: 14.4(kbps), down: 14.4(kbps))
        SCSD = 'scsd'       # HSCSD (up: 14.4, down: 57.6)
        GPRS = 'gprs'       # GPRS (up: 28.8, down: 57.6)
        EDGE = 'edge'       # EDGE/EGPRS (up: 473.6, down: 473.6)
        UMTS = 'umts'       # UMTS/3G (up: 384.0, down: 384.0)
        HSDPA = 'hsdpa'     # HSDPA (up: 5760.0, down: 13,980.0)
        LTE = 'lte'         # LTE (up: 58,000, down: 173,000)
        EVDO = 'evdo'       # EVDO (up: 75,000, down: 280,000)
        FULL = 'full'       # No limit, the default (up: 0.0, down: 0.0)
        :param speed:
        :return:
        """
        self.__driver.set_network_speed(speed)

    def start_recording(self):
        self.driver.start_recording_screen()

    def stop_recording(self):
        self.driver.stop_recording_screen()

    def get_device_time(self, formater="YYYY-MM-DD LTS"):
        """
        Format	                    Example
        YYYY-MM-DDTHH:mm	        2017-12-14T16:34
        YYYY-MM-DDTHH:mm:ss	        2017-12-14T16:34:10
        YYY-MM-DDTHH:mm:ss.SSS	    2017-12-14T16:34:10.234
        YYYY-MM-DD	                2017-12-14
        HH:mm	                    16:34
        HH:mm:ss	                16:34:10
        HH:mm:ss.SSS	            16:34:10.234
        YYYY-[W]WW	                2017-W50
        YYYY-MM	                    2017-12
        :return:
        """
        return self.driver.get_device_time(formater)


if __name__ == '__main__':
    server = "http://192.168.1.16:4723/wd/hub"

    setting = {
        "deviceName": "127.0.0.1:62001",
        "platformVersion": "5.1.1",
        "appPackage": "com.chinat2t32275yuneb.templte",
        "platformName": "Android",
        "noReset": "true",
        "appActivity": "com.chinat2t.tp005.activity.SplashActivity",
        # "automationName":"Selendroid",
    }
    s = requests.get(server + "/status")
    print(s.text)
