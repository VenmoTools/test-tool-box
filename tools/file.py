import csv
import os
import platform
import re

from tools.date import DateTime


class FileUtil:
    __slots__ = []

    @classmethod
    def delete(cls, path):
        # 如果文件不存在则不做处理
        if not os.path.exists(path):
            return
        # 循环当前所有的文件夹
        for file in os.listdir(path):
            # 根据当前路径拼接 文件路径
            file_path = os.path.join(path, file)
            # 如果是文件直接删除
            if os.path.isfile(file_path):
                os.remove(file_path)
            # 如果是文件夹则删除当前文件夹内容，然后删除该文件夹
            elif os.path.isdir(path):
                cls.delete(file_path)
                os.rmdir(file_path)
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            os.rmdir(path)

    @classmethod
    def mkdir(cls, name):
        if os.path.exists(name):
            return name
        os.mkdir(name)
        return name

    @classmethod
    def mkdirs(cls, path):
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def current_date_dir(cls):
        return cls.mkdir(DateTime.current_date())

    @classmethod
    def path_join(cls, p1, p2):
        return os.path.join(p1, p2)

    @classmethod
    def get_current_os(cls):
        current_system = platform.platform()
        return current_system[:current_system.index("-")]

    @classmethod
    def check_execute_able_path(cls, path):
        file = path

        if cls.get_current_os().lower() == "windows":
            try:
                file = re.findall(r"\\([\w\d.]+?)$", path)[0]
            except IndexError:
                raise TypeError("{}路径不符合格式".format(path))
            if not re.match(".+?exe$", file):
                return path + ".exe"
            return path
        elif cls.get_current_os().lower() == "linux":
            if "\\" in path:
                path = path.replace("\\", "/")
            if ":" in path:
                path = path[path.index(":") + 1:]
            if re.match(".+?exe$", file):
                return path[:len(path) - 4]
            return path
        else:
            raise SystemError("不支持当前系统")

    @classmethod
    def read_csv_file(cls, filename):
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            return [row for row in reader]
