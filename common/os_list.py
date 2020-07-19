import platform
from enum import Enum


class System(Enum):
    Linux = "linux"
    MacOs = "darwin"
    Windows = "windows"
    Netbsd = "netbsd"
    Openbsd = "openbsd"
    Cloudabi = "cloudabi"
    Emscripten = "emscripten"
    NoSupport = "not support"

    @classmethod
    def get_current_os(cls):
        current_system = platform.platform()
        os = current_system[:current_system.index("-")].lower()
        for attr, va in cls.__dict__.items():
            if attr == "_value2member_map_":
                try:
                    return va[os]
                except KeyError:
                    pass
        return System.NoSupport


if __name__ == '__main__':
    print(System.get_current_os())
