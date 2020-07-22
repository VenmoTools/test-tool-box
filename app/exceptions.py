class CommonUsbError(Exception):
    """Base class for usb communication errors."""


class FormatMessageWithArgumentsException(CommonUsbError):
    def __init__(self, message, *args):
        message %= args
        super(FormatMessageWithArgumentsException, self).__init__(message, *args)


class DeviceNotFoundError(FormatMessageWithArgumentsException):
    """Device isn't on USB."""


class DeviceAuthError(FormatMessageWithArgumentsException):
    """Device authentication failed."""


class SettingNoFound(FormatMessageWithArgumentsException):
    """No settings found from given setting"""


class LibusbWrappingError(CommonUsbError):
    """Wraps libusb1 errors while keeping its original usefulness.

    Attributes:
      usb_error: Instance of libusb1.USBError
    """

    def __init__(self, msg, usb_error):
        super(LibusbWrappingError, self).__init__(msg)
        self.usb_error = usb_error

    def __str__(self):
        return '%s: %s' % (
            super(LibusbWrappingError, self).__str__(), str(self.usb_error))


class WriteFailedError(LibusbWrappingError):
    """Raised when the device doesn't accept our command."""


class ReadFailedError(LibusbWrappingError):
    """Raised when the device doesn't respond to our commands."""


class AdbCommandFailureException(Exception):
    """ADB Command returned a FAIL."""


class AdbOperationException(Exception):
    """Failed to communicate over adb with device after multiple retries."""


class InvalidCommandError(Exception):
    """Got an invalid command over USB."""

    def __init__(self, message, response_header, response_data):
        if response_header == b'FAIL':
            message = 'Command failed, device said so. (%s)' % message
        super(InvalidCommandError, self).__init__(
            message, response_header, response_data)


class InvalidResponseError(Exception):
    """Got an invalid response to our command."""


class InvalidChecksumError(Exception):
    """Checksum of data didn't match expected checksum."""


class InterleavedDataError(Exception):
    """We only support command sent serially."""
