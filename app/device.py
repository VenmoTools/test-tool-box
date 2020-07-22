import abc
from typing import List, Union

import usb1

from app.connector import USBConnector

CLASS = 0xFF
SUBCLASS = 0x42
PROTOCOL = 0x01


class Matcher(metaclass=abc.ABCMeta):
    __slots__ = ["other"]

    def __init__(self, other):
        self.other = other

    @abc.abstractmethod
    def __call__(self, devices: usb1.USBDevice) -> Union[bool, List[usb1.USBInterfaceSetting]]:
        pass


class SerialMatcher(Matcher):

    def __call__(self, devices: usb1.USBDevice) -> bool:
        return self.other == devices.getSerialNumber()


class InterfaceMatcher(Matcher):

    def __call__(self, devices: usb1.USBDevice) -> Union[bool, List[usb1.USBInterfaceSetting], None]:
        def unpack(setting: usb1.USBInterfaceSetting):
            return setting.getClass(), setting.getSubClass(), setting.getProtocol()

        assert isinstance(self.other, tuple), f"interface matcher require tuple type"
        for settings in devices.iterSettings():
            if unpack(settings) == self.other:
                return settings
        # raise SettingNoFound(f"not setting found use given setting {self.other}")
        return None


AVAILABLE_DEVICE = InterfaceMatcher((CLASS, SUBCLASS, PROTOCOL))


def serial_matcher(serial) -> Matcher:
    return SerialMatcher(serial)


def get_devices(setting_matcher: Matcher, device_matcher=None, usb_info='', timeout_ms=None) -> USBConnector:
    ctx = usb1.USBContext()
    for usb_devices in ctx.getDeviceList(skip_on_error=True):
        match = setting_matcher(usb_devices)
        if not match:
            continue
        if isinstance(match, usb1.USBInterfaceSetting):
            return USBConnector(match, device_matcher, usb_info=usb_info, timeout=timeout_ms)
        else:
            print(f"not settings {match}")
