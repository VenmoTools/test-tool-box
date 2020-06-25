class Time:
    NanoSecond = "NS"
    MicroSecond = "μS"
    MilliSecond = "MS"
    Second = "Sec"
    Minutes = "Min"
    Hour = "Hour"
    Day = "Day"
    Month = "Mon"
    Year = "Year"


class StorageUnit:
    Bit = "Bit"  # 比特
    Byte = "B"  # 字节
    KiloByte = "KB"  # 千字节
    MegaByte = "MB"  # 兆字节
    GigaByte = "GB"  # 吉字节
    TeraByte = "TB"  # 太字节
    PetaByte = "PB"  # 拍字节
    ExaByte = "EB"  # 艾字节
    ZettaByte = "ZB"  # 泽字节
    YottaByte = "YB"  # 尧字节
    BrontoByte = "BB"  # “千秭”字节


class Math:

    @classmethod
    def computer_size_unit_convert(cls, number, select_unit="B"):
        """
        默认使用byte单位
        1024b -> 1kb
        :param number: 转换值
        :param select_unit: 转换单位
        :return:
        """
        unit = ["Bit", "B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB", "BB"]
        index = unit.index(select_unit)
        if index == 0:
            # number /= 8 2^3
            number = number >> 3
            index += 1
        while int(number) >= 1024:
            """
            除法  2.615910530090332e-06   / loop  1000000     Total   2.78Sec
            位移  2.326258420944214e-06S  / loop  1000000     Total   2.52Sec        
            """
            # number /= 1024
            number = number >> 10
            if index > len(unit) - 2:
                break
            index += 1
        return "%.2f%s" % (number, unit[index])

    @classmethod
    def time_convert(cls, number, select_unit="NS"):
        """
        NS = 纳秒
        μS =微秒
        MS = 毫秒
        S = 秒
        M = 分
        H = 时
        1000纳秒 = 1微秒
        1000微秒 = 1毫秒
        1000毫秒 = 1秒
        60秒=1分钟
        60分钟=1小时
        :param number: 转换值
        :param select_unit: 转换单位
        :return:
        """
        unit = ["NS", "μS", "MS", "Sec", "Min", "Hour", "Day", "Mon", "Year"]
        index = unit.index(select_unit)

        while int(number) > 1000 and index < 2:
            number /= 1000
            index += 1

        while int(number) > 60 and index < 5:
            number /= 60
            index += 1

        if int(number) > 24 and index < 6:
            number /= 24
            index += 1

        if int(number) > 30 and index < 7:
            number /= 30
            index += 1

        if int(number) > 12 and index < 8:
            number /= 12
            index += 1

        return "%.2f%s" % (number, unit[index])

    @classmethod
    def time_to_second(cls, number, select_unit=Time.Minutes):
        result = {
            Time.Second: "{}".format(number),
            Time.Minutes: "{}*60".format(number),
            Time.Hour: "{}*3600".format(number),
            Time.Day: "{}*3600*24".format(number),
        }
        result[Time.Year] = "{}*365".format(result[Time.Day])
        try:
            return eval(result[select_unit])
        except KeyError:
            print("{} not support".format(select_unit))
