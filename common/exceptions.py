class AdbNoStartError(Exception):
    pass


class NoSuchProcessNameError(Exception):
    pass


class CommandError(Exception):
    pass


class ConfigError(Exception): pass


class PlatformNoSupport(Warning):
    """ Base class for warnings about deprecated features. """
    pass
