import re
from configparser import ConfigParser
from typing import List, Any

from cryptography import x509
from cryptography.hazmat._oid import ObjectIdentifier
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.backends.openssl.rsa import _RSAPrivateKey
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import NameOID

CONFIG_INI = """
[X509Name]
country_name=US # require
state_or_province_name=California # require 
locality_name=San Francisco # require
organization_name=My Company # require
common_name=mysite.com # require
street_address=What ever
postal_code=94101
postal_address=California, San Francisco County, San Mateo County
organizational_unit_name=
serial_number=
surname=
given_name=
title=
generation_qualifier=
x500_unique_identifier=
dn_qualifier=
pseudonym=
user_id=
domain_component=
email_address=
jurisdiction_country_name=
jurisdiction_locality_name=
jurisdiction_state_or_province_name=
business_category=


[AlternativeName]
dns = ["example.com","abc.com"]
"""


class X509Name:

    def __init__(self, config: ConfigParser):
        self.config = config
        self.current_section = "X509Name"

    def collect(self) -> List[x509.NameAttribute]:
        attrs = [x.lower() for x in NameOID.__dict__ if "__" not in x]
        return [getattr(self, f"x509_{attr}")(self.config.get(self.current_section, attr).encode()) for attr in attrs if
                self.config.get(self.current_section, attr)]

    @staticmethod
    def x509name_attr(attr: ObjectIdentifier, data: bytes):
        return x509.NameAttribute(attr, data)

    def x509_country_name(self, data: bytes):
        return self.x509name_attr(NameOID.COUNTRY_NAME, data)

    def x509_state_or_province_name(self, data: bytes):
        return self.x509name_attr(NameOID.COUNTRY_NAME, data)

    def x509_common_name(self, data: bytes):
        return self.x509name_attr(NameOID.COMMON_NAME, data)

    def x509_locality_name(self, data: bytes):
        return self.x509name_attr(NameOID.LOCALITY_NAME, data)

    def x509_street_address(self, data: bytes):
        return self.x509name_attr(NameOID.STREET_ADDRESS, data)

    def x509_organization_name(self, data: bytes):
        return self.x509name_attr(NameOID.ORGANIZATION_NAME, data)

    def x509_organizational_unit_name(self, data: bytes):
        return self.x509name_attr(NameOID.ORGANIZATIONAL_UNIT_NAME, data)

    def x509_serial_number(self, data: bytes):
        return self.x509name_attr(NameOID.SERIAL_NUMBER, data)

    def x509_surname(self, data: bytes):
        return self.x509name_attr(NameOID.SURNAME, data)

    def x509_given_name(self, data: bytes):
        return self.x509name_attr(NameOID.GIVEN_NAME, data)

    def x509_title(self, data: bytes):
        return self.x509name_attr(NameOID.TITLE, data)

    def x509_generation_qualifier(self, data: bytes):
        return self.x509name_attr(NameOID.GENERATION_QUALIFIER, data)

    def x509_x500_unique_identifier(self, data: bytes):
        return self.x509name_attr(NameOID.X500_UNIQUE_IDENTIFIER, data)

    def x509_dn_qualifier(self, data: bytes):
        return self.x509name_attr(NameOID.DN_QUALIFIER, data)

    def x509_pseudonym(self, data: bytes):
        return self.x509name_attr(NameOID.PSEUDONYM, data)

    def x509_user_id(self, data: bytes):
        return self.x509name_attr(NameOID.USER_ID, data)

    def x509_domain_component(self, data: bytes):
        return self.x509name_attr(NameOID.DOMAIN_COMPONENT, data)

    def x509_email_address(self, data: bytes):
        return self.x509name_attr(NameOID.EMAIL_ADDRESS, data)

    def x509_jurisdiction_country_name(self, data: bytes):
        return self.x509name_attr(NameOID.JURISDICTION_COUNTRY_NAME, data)

    def x509_jurisdiction_locality_name(self, data: bytes):
        return self.x509name_attr(NameOID.JURISDICTION_LOCALITY_NAME, data)

    def x509_jurisdiction_state_or_province_name(self, data: bytes):
        return self.x509name_attr(NameOID.JURISDICTION_STATE_OR_PROVINCE_NAME, data)

    def x509_business_category(self, data: bytes):
        return self.x509name_attr(NameOID.BUSINESS_CATEGORY, data)

    def x509_postal_address(self, data: bytes):
        return self.x509name_attr(NameOID.POSTAL_ADDRESS, data)

    def x509_postal_code(self, data: bytes):
        return self.x509name_attr(NameOID.POSTAL_CODE, data)


class X509SubjectAlternativeName:

    def __init__(self, config: ConfigParser):
        self.config = config
        self.current_section = "AlternativeName"
        self.attr = "dns"

    def collect(self) -> List[Any]:
        res = re.findall(r"([\d\w.]+)", self.config.get(self.current_section, self.attr))
        return [x509.DNSName(attr) for attr in res]


class X509Cert:

    @staticmethod
    def generate_private_key(key_size, backend=None, public_exponent=65537) -> _RSAPrivateKey:
        """
        生成RSA秘钥
        :param key_size:  bits 是一个字节大小的值，必须大于等于1024，通常建议写1024的倍数，FIPS定义了1024，2048， 3072。
        :param backend: 默认就好
        :param public_exponent:  e=65537 是公共 RSA 指数，它必须是一个正整数。FIPS 标准要求公共指数至少65537(默认)
        :return:
        """
        return rsa.generate_private_key(public_exponent, key_size,
                                        backend=default_backend() if backend is None else backend())

    @staticmethod
    def save_private_key(filename, key: _RSAPrivateKey):
        """
        保存生成的RSA秘钥
        :param filename: 文件路径
        :param key: 生成的秘钥
        :return:
        """
        with open(filename, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.BestAvailableEncryption,
            ))

    @staticmethod
    def generate_csr(private_key, name: X509Name, subject: X509SubjectAlternativeName):
        return x509.CertificateSigningRequestBuilder().subject_name(x509.Name(name.collect())) \
            .add_extension(x509.SubjectAlternativeName(subject.collect()), critical=False) \
            .sign(private_key,
                  hashes.SHA3_256(),
                  default_backend())

    @staticmethod
    def save_csr_file(csr_file_name, csr, encoding=serialization.Encoding.PEM):
        with open(csr_file_name, 'wb') as f:
            f.write(csr.public_bytes(encoding))


if __name__ == '__main__':
    with open("example.ini", "w") as f:
        f.write(CONFIG_INI)
