import io
import os
import re
import subprocess
import sys

from app.key_event import KeyEventMixin
from common.exceptions import AdbNoStartError, NoSuchProcessNameError
from tools.file import FileUtil


class Devices:

    def __init__(self, status):
        self.serial_no, self.status = status

    def __str__(self):
        return "serial_no:{0},status:{1}".format(self.serial_no, self.status)

    def can_user(self):
        return self.status == "device"


class Parser:

    def parse(self, data, kind):
        if not data.kind():
            print("`{}`没有返回数据".format(kind), file=sys.stderr)
            return ""
        return getattr(self, kind)(data.stdout)

    @staticmethod
    def app_start_time(data):
        times = re.findall("(\w\d): (\d+)", data)
        return {k.replace(" ", ""): v for k, v in times}

    @staticmethod
    def start_server(data):
        print(data)

    @staticmethod
    def stop_server(data):
        print(data)

    @staticmethod
    def pid(data):
        lines = data.split("\n")
        if len(lines) == 0:
            raise NoSuchProcessNameError("进程名没有找到")
        return [re.findall(".*[\d\w]_+(\d+?)_.+[SR]_([\w.\d:]+)", line.replace(" ", "_"))[0] for line in lines if
                line != ""]

    @staticmethod
    def network_flow(data):
        lines = data.split("\n")
        result = []
        for line in lines:
            all_number = re.findall("(\d+)", line[line.index(":") + 1:])
            result.append((int(all_number[0]), int(all_number[8])))
        return result

    @staticmethod
    def battery_info(data):
        res = re.findall("(.+): (.+)", data)
        res = {k.replace(" ", ""): v for k, v in res}
        return res

    @staticmethod
    def cpu_info(data):
        return int(re.findall("(\d+)%.+", data)[0])

    @staticmethod
    def current_activity(data):
        lines = data.split("\n")
        all_activity = [re.findall(".*cmp=([\w.]+)/([\w.]+).*}", line)[0] for line in lines if "cmp=" in line]
        assert len(all_activity) > 0
        return all_activity[len(all_activity) - 1]

    @staticmethod
    def devices(data):
        if "*" in data:
            raise AdbNoStartError("Adb服务没有启动")
        lines = data.split("\n")
        devices = []
        for line in lines:
            if line.startswith("List of"):
                continue
            c = re.findall("(.+).+(device|offline|unknown)", line)
            if len(c) != 0:
                devices.append(Devices(c[0]))
        return devices


parse = Parser()


class AppMixin:
    __slots__ = ()

    def force_stop_app(self, package_name) -> None:
        """
        停止当前app
        :param package_name: 包名
        :return:
        """
        self.adb_shell("am force-stop {}".format(package_name))

    def start_app(self, package_name, activity_name) -> None:
        """
        启动app
        :param package_name:  包名
        :param activity_name:  app的activity_name
        :return:
        """
        self.adb_shell("am start -n {0}/{1}".format(package_name, activity_name))

    def get_all_packages(self) -> list:
        """
        获取所有的包包含系统的和第三方的
        :return:
        """
        return self.adb_shell("pm list packages").split("\n")

    def get_all_system_packages(self) -> list:
        """
        获取所有包系统的包
        :return:
        """
        return self.adb_shell("pm list packages -s").split("\n")

    def get_all_third_packages(self) -> list:
        """
        获取所有包第三方的包
        :return:
        """
        return self.adb_shell("pm list packages -3").split("\n")

    def clear_package_data(self, package_name) -> None:
        self.adb_shell("pm clear {}".format(package_name))

    def get_current_package_activity(self):
        """
        获取当前的包的activity
        :return:
        """
        return parse.parse(self.execute_adb('logcat -d | {} "START"'.format(os_grep())), "current_activity")

    def get_app_start_time(self, app_name: str, activity: str):
        """
        获取App启动时间
        :param app_name:  App名
        :param activity:  App的Activity
        :return: 返回启动时间单位毫秒
        """
        return parse.parse(self.adb_shell("am start -W -n {0}/{1}".format(app_name, activity)),
                           "app_start_time")


class ServerMixin:
    __slots__ = ()

    def start_server(self):
        return parse.parse(self.execute_adb("start-server"), "start_server")

    def stop_server(self):
        return parse.parse(self.execute_adb("kill-server"), "stop_server")


class PhysicalDeviceMixin:
    __slots__ = ()

    def change_charging_status(self, status):
        if isinstance(status, str):
            status = int(status)
        if isinstance(status, int):
            assert 0 <= status < 10, "状态必须在0-10之间"
        self.adb_shell("dumpsys battery set status {}".format(status))

    def get_device_battery_info(self):
        return parse.parse(self.adb_shell("dumpsys battery"), "battery_info")

    def get_pid(self, package_name: str):
        return parse.parse(self.adb_shell('ps | {0} "{1}"'.format(os_grep(), package_name)), "pid")

    def get_network_flow(self, package_name: str, index=-1):
        all_pid = self.get_pid(package_name)
        assert len(all_pid) >= 1, "没有找到`{}`进程".format(package_name)
        if index < 0:
            return [parse.parse(self.adb_shell("cat /proc/{}/net/dev".format(pid)),
                                "network_flow") for pid, name in all_pid]
        pid, name = all_pid[index]
        return parse.parse(self.adb_shell("cat /proc/{}/net/dev".format(pid)),
                           "network_flow")

    def get_cpu_info(self, package_name):
        return parse.parse(self.adb_shell('dumpsys cpuinfo | {0} "{1}"'.format(os_grep(), package_name)), "cpu_info")


def os_grep():
    return "find" if FileUtil.get_current_os().lower() == "windows" else "grep"


class Message:

    def __init__(self):
        self.stdout = ""
        self.stderr = ""

    def return_out_or_err(self):
        return self.stdout if self.stdout else self.stderr

    def kind(self):
        return self.stdout != "" and self.stderr == ""


class AndroidDebugBridge(PhysicalDeviceMixin, ServerMixin, KeyEventMixin, AppMixin):

    def __init__(self, path):
        self.check_and_set(path)

    @staticmethod
    def check_and_set(path):
        if not os.path.exists(path):
            raise ValueError("`{}` do not exists".format(path))
        if not os.path.isfile(path):
            raise ValueError("`{}` is not file".format(path))
        if not os.path.isabs(path):
            raise ValueError("`{}` is not absolute path".format(path))
        os.environ["adb"] = path

    @staticmethod
    def execute_script(cmd: str, buffering=-1) -> Message:
        if not isinstance(cmd, str):
            raise TypeError("invalid cmd type (%s, expected string)" % type(cmd))
        if buffering == 0 or buffering is None:
            raise ValueError("popen() does not support unbuffered streams")
        proc = subprocess.Popen(cmd,
                                shell=True,
                                stdout=subprocess.PIPE,
                                bufsize=buffering)
        msg = Message()
        wrapper = io.TextIOWrapper(proc.stdout)
        if wrapper:
            msg.stdout = wrapper.read()
        wrapper.close()
        proc.wait()
        return msg

    def execute_adb(self, cmd: str) -> Message:
        return self.execute_script("{0} {1}".format(os.getenv("adb"), cmd))

    def adb_shell(self, cmd: str) -> Message:
        return self.execute_script("{0} shell {1}".format(os.getenv("adb"), cmd))

    def adb_version(self) -> str:
        """
        获取ADB的版本信息
        :return:
        """
        return self.execute_adb("version").return_out_or_err()

    def device_size(self) -> str:
        """
        获取屏幕尺寸
        :return:
        """
        return self.adb_shell("wm size").return_out_or_err()

    def device_density(self) -> str:
        return self.adb_shell("wm density").return_out_or_err()

    def get_mac_address(self, net_card="wlan0") -> str:
        """
        获取Mac地址
        :return:
        """
        return self.adb_shell("cat /sys/class/net/{}/address".format(net_card)).return_out_or_err()

    def device_model(self) -> str:
        """
        获取设备型号
        :return:
        """
        return self.adb_shell(" getprop ro.product.model").return_out_or_err()

    def device_android_version(self) -> str:
        return self.adb_shell("getprop ro.build.version.release").return_out_or_err()

    def get_devices(self) -> list:
        """
        获取所有设备信息，包含链接的和未连接的
        :return:
        """
        return parse.parse(self.execute_adb("devices"), "devices")
