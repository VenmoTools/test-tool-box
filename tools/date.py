import time


class DateTime:
    __slots__ = []
    TimeCol = {
        "YEAH": 60 * 60 * 24 * 12,
        "DAYS": 60 * 60 * 24,
        "HOURS": 60 * 60,
        "MINUTES": 60,
        "SECONDS": 1
    }

    @classmethod
    def current_time(cls, partten="%H:%M:%S"):
        local = time.localtime(time.time())
        return time.strftime(partten, local)

    @classmethod
    def current_date(cls):
        return cls.current_time(partten="%Y-%m-%d")

    @classmethod
    def years_later(cls, years, strf="%Y-%m-%d %H:%M:%S"):
        return cls.time_later("YEARS", years, strf)

    @classmethod
    def days_later(cls, days, strf="%Y-%m-%d %H:%M:%S"):
        """
        获取当前日期days天后日期
        :param days:
        :return:
        """
        return cls.time_later("DAYS", days, strf)

    @classmethod
    def hours_later(cls, hours, strf="%Y-%m-%d %H:%M:%S"):
        """
        获取当前日期hours小时后日期
        :param hours:
        :return:
        """
        return cls.time_later("HOURS", hours, strf)

    @classmethod
    def seconds_later(cls, sec, strf="%Y-%m-%d %H:%M:%S"):
        """
        获取当前日期sec秒后日期
        :param sec:
        :param strf:
        :return:
        """
        return cls.time_later("SECONDS", sec, strf)

    @classmethod
    def minutes_later(cls, mins, strf="%Y-%m-%d %H:%M:%S"):
        """
        获取当前日期sec秒后日期
        :param mins:
        :param strf:
        :return:
        """
        return cls.time_later("MINUTES", mins, strf)

    @classmethod
    def time_later(cls, types, times, strf="%Y-%m-%d %H:%M:%S"):
        if isinstance(times, str):
            times = int(times)
        if times < 0:
            times = 0
        later = time.time() + cls.TimeCol[types] * times
        if later <= 0:
            raise TimeError("指定时间错误")
        return time.strftime(strf, time.localtime(later))

    @classmethod
    def time_before(cls, types, times, strf="%Y-%m-%d %H:%M:%S"):
        if isinstance(times, str):
            times = int(times)
        if times < 0:
            times = 0
        later = time.time() - times * cls.TimeCol[types]
        if later <= 0:
            raise TimeError("指定时间错误")
        return time.strftime(strf, time.localtime(later))

    @classmethod
    def days_before(cls, days, strf="%Y-%m-%d %H:%M:%S"):
        """
        获取当前日期days天后日期
        :param days:
        :return:
        """
        return cls.time_before("DAYS", days, strf)

    @classmethod
    def minutes_before(cls, mins, strf="%Y-%m-%d %H:%M:%S"):
        """
        获取当前日期days天后日期
        :param mins:
        :return:
        """
        return cls.time_before("MINUTES", mins, strf)

    @classmethod
    def seconds_before(cls, sec, strf="%Y-%m-%d %H:%M:%S"):
        return cls.time_before("SECONDS", sec, strf)

    @classmethod
    def current_date_time(cls):
        return cls.current_time(partten="%Y-%m-%d %H:%M:%S")

    @classmethod
    def time_it(cls, func, *args, **kwargs):
        start_time = time.time()
        func(*args, **kwargs)
        end_time = time.time()
        return end_time - start_time


class TimeError(Exception):
    pass
