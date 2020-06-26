import abc
import base64
import binascii
import functools
import hashlib
import os
from typing import Union
from urllib import parse

from Crypto import Random
from Crypto.Cipher import DES, PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5 as PKCS1_SIN

from tools import bug

# crypto，pycrypto，pycryptodome的功能是一样的。crypto与pycrypto已经没有维护了，后面可以使用pycryptodome。
# pip install pycryptodome 安装之前，最好先把 crypto 和 pycrypto 卸载了(uninstall)，避免不必要的麻烦

_MAXCACHE = 512


class Key(metaclass=abc.ABCMeta):

    def __init__(self, rsa, key_func):
        self._rsa = rsa
        self.__key_func = key_func

    @functools.lru_cache(_MAXCACHE)
    def get_keys(self, format='PEM', passphrase=None, pkcs=1,
                 protection=None, randfunc=None) -> bytes:
        return self.__key_func(format, passphrase, pkcs, protection, randfunc)

    def to_file(self, filename):
        with open(filename, 'wb') as fp:
            fp.write(self.get_keys())

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'rb') as fp:
            key = RSA.import_key(fp.read())
            return cls(key, key.export_key)

    @property
    def inner(self) -> RSA:
        return self._rsa


class RsaPrivateKey(Key):
    pass


class RsaPublicKey(Key):
    pass


class RSAEncryption:

    @classmethod
    def generate_rsa_private_key(cls, bits, e=65537):
        """
        :param e: e=65537 是公共 RSA 指数，它必须是一个正整数。FIPS 标准要求公共指数至少65537(默认)
        :param bits: bits 是一个字节大小的值，必须大于等于1024，通常建议写1024的倍数，FIPS定义了1024，2048， 3072。
        :return:
        """
        random = Random.new().read
        rsa = RSA.generate(bits, random, e)
        return RsaPrivateKey(rsa, rsa.export_key), RsaPublicKey(rsa, rsa.publickey().export_key)

    @classmethod
    @functools.lru_cache(_MAXCACHE)
    def encrypt(cls, key: Union[RsaPublicKey, str], content: bytes, need_base64=True):
        if isinstance(key, str) and os.path.isfile(key):
            key = RsaPublicKey.from_file(key)
        enc = PKCS1_v1_5.new(key.inner)
        if not enc.can_encrypt():
            raise ValueError(" cipher object can not encrypted")
        enc_content = enc.encrypt(content)
        return Encryption.base64_encode(enc_content) if need_base64 else enc_content

    @classmethod
    @functools.lru_cache(_MAXCACHE)
    def decrypt(cls, key: Union[RsaPrivateKey, str], encrypted_content, has_base64=True):
        if isinstance(key, str) and os.path.isfile(key):
            key = RsaPublicKey.from_file(key)
        content = Encryption.base64_decode(encrypted_content) if has_base64 else encrypted_content
        enc = PKCS1_v1_5.new(key.inner)
        return enc.decrypt(content, 0)

    @classmethod
    @functools.lru_cache(_MAXCACHE)
    def signature(cls, key: Union[RsaPrivateKey, str], content: bytes, need_base64=True):
        if isinstance(key, str) and os.path.isfile(key):
            key = RsaPublicKey.from_file(key)
        sign = PKCS1_SIN.new(key.inner).sign(SHA.new(content))
        return Encryption.base64_encode(sign) if need_base64 else sign

    @bug("signature_verify")
    @classmethod
    @functools.lru_cache(_MAXCACHE)
    def signature_verify(cls, key: RsaPublicKey, encrypted_content: bytes, has_base64=True) -> bool:
        content = Encryption.base64_decode(encrypted_content) if has_base64 else encrypted_content
        sign = PKCS1_SIN.new(key.inner)
        try:
            sign.verify(SHA.new(content), content)
            return True
        except ValueError:
            return False


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


if __name__ == '__main__':
    private, public = RSAEncryption.generate_rsa_private_key(2048)
    cont = '需要加密的信息'
    res = RSAEncryption.encrypt(public, cont.encode())
    res = RSAEncryption.decrypt(private, res)
    print(res.decode())
    res = RSAEncryption.signature(private, cont.encode())
    RSAEncryption.signature_verify(public, res)
