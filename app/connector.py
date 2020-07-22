import abc
import logging
import threading
import weakref
from typing import Union

import usb1
from usb1 import libusb1

from app.exceptions import ReadFailedError, WriteFailedError
from common import System


class BasicConnector(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def open(self):
        pass

    @abc.abstractmethod
    def close(self):
        pass

    @abc.abstractmethod
    def write(self, data: bytes, timeout=None):
        pass

    @abc.abstractmethod
    def read(self, length: int, timeout=None):
        pass

    def timeout_second(self, timeout):
        if hasattr(self, "_timeout"):
            timeout = float(timeout) / 1000.0 if timeout else getattr(self, "_timeout")
        return timeout

    @abc.abstractmethod
    def flush(self):
        pass


class USBConnector(BasicConnector):
    _device_handle: Union[usb1.USBDeviceHandle, None]

    _LOCK_ = threading.Lock()
    _CACHE_ = weakref.WeakValueDictionary()

    def __init__(self, setting: usb1.USBInterfaceSetting, device: usb1.USBDevice, usb_info=None, timeout=None):
        self._usb_info = usb_info
        self._timeout = timeout
        self._device = device
        self._setting = setting
        self._port_path = None
        self._read_endpoint = None
        self._write_endpoint = None
        self._max_read_packet_len = 0
        self._device_handle = None
        self._interface_number = None
        self._flush_buffer = bytearray()

    @property
    def serial_number(self):
        return self._device.getSerialNumber()

    @property
    def usb_info(self):
        try:
            sn = self.serial_number
        except usb1.USBError:
            sn = ""
        if sn and sn != self._usb_info:
            return f"{self._usb_info} {sn} "
        return self._usb_info

    def open(self):
        assert self._port_path is not None, "require device port path"
        port_path = tuple(self._port_path)
        with self._LOCK_:
            old_handle = self._CACHE_.get(port_path)
            if old_handle is not None:
                old_handle.Close()

        for endpoint in self._setting.iterEndpoints():
            address = endpoint.getAddress()
            if self.is_read_endpoint(address):
                self._read_endpoint = address
                self._max_read_packet_len = endpoint.getMaxPacketSize()
            else:
                self._write_endpoint = address

        self.check_endpoint()
        device_handle = self._device.open()
        ifcae_no = self._setting.getNumber()

        try:
            if System.get_current_os() != System.Windows and device_handle.kernelDriverActive(ifcae_no):
                device_handle.attachKernelDriver(ifcae_no)
        except usb1.USBError as e:
            if e.value == libusb1.LIBUSB_ERROR_NOT_FOUND:
                logging.warning(f'Kernel driver not found for interface: {ifcae_no}.')
            else:
                raise

        device_handle.claimInterface(ifcae_no)
        self._device_handle = device_handle
        self._interface_number = ifcae_no

        with self._LOCK_:
            self._CACHE_[port_path] = self

        # When this object is deleted, make sure it's closed.
        # 但该对象被删除后由于weak ref的存在 依旧可以调用Close方法
        weakref.ref(self, self.close)

    def check_endpoint(self):
        assert self._write_endpoint is not None, "No Write endpoint found!"
        assert self._read_endpoint is not None, "No Read endpoint found!"

    @staticmethod
    def is_read_endpoint(address):
        return address & libusb1.USB_ENDPOINT_DIR_MASK

    def close(self):
        if self._device_handle is None:
            return

        assert self._interface_number is not None, "got None interface number when close device"
        try:
            self._device_handle.releaseInterface(self._interface_number)
            self._device_handle.close()
        except usb1.USBError:
            logging.info('USBError while closing handle %s: ',
                         self.usb_info, exc_info=True)
        finally:
            self._device_handle = None

    def write(self, data: bytes, timeout=None):
        if self._device_handle is None:
            raise WriteFailedError(
                'This handle has been closed, probably due to another being opened.',
                None)
        timeout = self.timeout_second(timeout)
        try:
            self._device_handle.bulkWrite(self._write_endpoint, data, timeout)
        except usb1.USBError as e:
            ReadFailedError(
                'An error occurred when write data to %s (timeout %sms)' % (
                    self.usb_info, timeout), e)

    def read(self, length: int, timeout=None):
        if self._device_handle is None:
            raise ReadFailedError(
                'This handle has been closed, probably due to another being opened.',
                None)
        timeout = self.timeout_second(timeout)
        try:
            return bytearray(self._device_handle.bulkRead(self._read_endpoint,
                                                          length,
                                                          timeout))
        except usb1.USBError as e:
            ReadFailedError(
                'Could not receive data from %s (timeout %sms)' % (
                    self.usb_info, timeout), e)

    def flush(self):
        while True:
            try:
                self._flush_buffer = self.read(self._max_read_packet_len, self._timeout)
            except ReadFailedError as e:
                if e.usb_error.value == libusb1.LIBUSB_ERROR_TIMEOUT:
                    break
                raise
