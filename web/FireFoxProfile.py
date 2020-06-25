from selenium.webdriver import FirefoxProfile

from tools.file import FileUtil


class FireFoxProfile:
    DOWNLOAD_TO_DESK_TOP = 0
    DOWNLOAD_TO_DEFAULT_PATH = 1
    DOWNLOAD_TO_CUSTOMER = 2

    def __init__(self):
        self.__profile = FirefoxProfile()

    def set_browser_download_path(self, path):
        path = FileUtil.mkdirs(path)
        r"""
        D:\c\x\a
        如果x文件夹和a文件夹都没有会下载到默认路径
        :param path:
        :return:
        """
        self.__profile.set_preference("browser.download.dir", path)
        return self

    def use_download_path(self, level):
        if not isinstance(level, int):
            raise ValueError("必须是整数")
        if level < 0 or level > 2:
            raise ValueError("参数必须小于2大于0")
        self.__profile.set_preference("browser.download.folderList", 2)
        return self

    def close_download_interface(self):
        """
        关闭下载界面
        :return:
        """
        self.__profile.set_preference("browser.download.manager.showWhenStarting", False)
        return self

    def close_download_window(self):
        """
        关闭下载窗口
        :return:
        """
        self.__profile.set_preference("browser.download.manager.useWindow", False)
        return self

    def close_focus(self):
        """
        关闭获取焦点
        :return:
        """
        self.__profile.set_preference("browser.download.manager.focusWhenStarting", False)
        return self

    def close_exe_file_alert(self):
        """
        关闭exe文件提示框
        :return:
        """
        self.__profile.set_preference("browser.download.manager.alertOnEXEOpen", False)
        return self

    def never_ask_open_file_mime(self, mime):
        """
        不会弹出指定文件类型的提示框
        :param mime: "application/pdf"
        :return:
        """
        self.__profile.set_preference("browser.helperApps.neverAsk.openFile", mime)
        return self

    def never_ask_save_to_disk(self, mime):
        """
        下载指定类型文件时不会提示下载到硬盘中
        :param mime:
        :return:
        """
        self.__profile.set_preference("browser.helperApps.neverAsk.saveToDisk", mime)
        return self

    def close_info_alert_when_download_finish(self):
        """
        下载完成时关闭提示
        :return:
        """
        self.__profile.set_preference("browser.download.manager.showAlertOnComplete", False)
        return self

    def dont_close_window_when_download_finish(self):
        """
        关闭下载结束时的提示框
        :return:
        """
        self.__profile.set_preference("browser.download.manager.closeWhenDone", False)
        return self

    def make(self):
        return self.__profile
