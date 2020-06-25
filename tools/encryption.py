import base64
import binascii
import hashlib
from urllib import parse

from Crypto import Random
from Crypto.Cipher import DES


class Encryption:

    @classmethod
    def url_encode(cls, url):
        """
        URL转码
        :param url:
        :return:
        """
        if isinstance(url, str):
            res = parse.quote(url)
        else:
            res = parse.quote_from_bytes(url)
        return res

    @classmethod
    def convert(cls, byte_string: str):
        if '0x' in byte_string:
            byte_string = byte_string.replace("0x", "\\x")
        return bytes(byte_string)

    @classmethod
    def url_decode(cls, data):
        """
        url解码
        :param data:
        :return:
        """
        return parse.unquote(data)

    @classmethod
    def base64_encode(cls, data):
        """
        base64加密
        :param data:
        :return:
        """
        if isinstance(data, str):
            data = bytes(data)
        return base64.b64encode(data)

    @classmethod
    def base64_decode(cls, data):
        """
        base64解密
        :param data:
        :return:
        """
        if isinstance(data, str):
            data = data.encode("utf8")
        return base64.decodebytes(data)

    @classmethod
    def md5_encode(cls, data):
        """
        MD5加密
        :param data:
        :return:
        """
        if isinstance(data, str):
            data = data.encode("utf8")
        elif isinstance(data, int):
            data = "{}".format(data)
        return hashlib.md5(data).hexdigest()

    @classmethod
    def des_encode(cls, key, data, mode="ecb"):
        """
        DES加密

        MODE_ECB（Electronic Codebook，电码本）模式是分组密码的一种最基本的工作模式。在该模式下，待处理信息被分为大小合适的分组，然后分别对每一分组独立进行加密或解密处理
        MODE_CBC 是一种循环模式，前一个分组的密文和当前分组的明文异或操作后再加密，这样做的目的是增强破解难度
        MODE_CFB CFB模式全称Cipher FeedBack模式（密文反馈模式）。在CFB模式中，前一个密文分组会被送回到密码算法的输入端。所谓反馈，这里指的就是返回输入端的意思
        MODE_OFB OFB模式:（Output Feedback）即输出反馈模式：明文模式被隐藏；分组密码的输入是随机的；用不同的IV，一个密钥可以加密多个消息；明文很容易被控制窜改，任何对密文的改变都会直接影响明文
        MODE_CTR 计数模式（CTR模式）加密是对一系列输入数据块(称为计数)进行加密，产生一系列的输出块，输出块与明文异或得到密文。
        MODE_OPENPGP 这种模式是CFB的一种变体，它只在PGP和OpenPGP应用程序中使用。需要一个初始化向量(IV)
        MODE_EAX 加密认证模式
        :param mode:
        :param key:
        :param data:
        :return:
        """
        mode = mode.lower()
        mode_key = {
            "ecb": DES.MODE_ECB,
            "cbc": DES.MODE_CBC,
            "cfb": DES.MODE_CFB,
            "ofb": DES.MODE_OFB,
            "ctr": DES.MODE_CTR,
            "openpgp": DES.MODE_OPENPGP,
            "eax": DES.MODE_EAX,
        }
        # ``MODE_CBC``, ``MODE_CFB``, and ``MODE_OFB``it must be 8 bytes long
        # (Only applicable for ``MODE_CBC``, ``MODE_CFB``, ``MODE_OFB``,
        #             and ``MODE_OPENPGP`` modes)
        data = data + ((8 - (len(data) % 8)) * '\0')
        if mode not in ["cbc", "cfb", "ofb", "openpgp"]:
            cipher = DES.new(key.encode(), mode_key[mode])
        else:
            vi = Random.new().read(DES.block_size)
            cipher = DES.new(key.encode(), mode_key[mode], vi)
        encrypt_data = cipher.encrypt(data.encode())
        return binascii.b2a_hex(encrypt_data)
