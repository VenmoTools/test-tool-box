import logging
import smtplib
import socket
import ssl
from email import message, utils, policy
from enum import Enum
from typing import Union, List, Dict, Tuple

from httpclient.strcutures import WithContext


class EmailStruct(Enum):
    FROM = "From"
    TO = "To"
    DATE = "Date"
    MSG_ID = "Message-ID"


class Email:

    def __init__(self, send_from, email_policy=policy.SMTP):
        self._msg = message.EmailMessage(email_policy)
        self._msg[EmailStruct.FROM.value] = send_from
        self._msg[EmailStruct.DATE.value] = utils.formatdate(localtime=True)
        self._msg[EmailStruct.MSG_ID.value] = utils.make_msgid()

    def __getitem__(self, item: EmailStruct):
        return self._msg[item.value]

    def to(self, data: Union[List[str], str]):
        self._msg[EmailStruct.TO.value] = self.convert_to_str(data)
        return self

    def set_email_charset(self, charset):
        self._msg.set_charset(charset)
        return self

    def content(self, msg):
        self._msg.set_content(msg)
        return self

    def subject(self, sub):
        self._msg["Subject"] = sub
        return self

    def to_message(self) -> bytes:
        return self._msg.as_bytes()

    @staticmethod
    def convert_to_str(data: Union[List[str], str]):
        if isinstance(data, str):
            return data
        return ", ".join(data)


@WithContext
class SMTPSender:

    def __init__(self, server, port):
        try:
            self._client = smtplib.SMTP(server, port)
        except (socket.gaierror, socket.error, socket.herror, smtplib.SMTPException) as e:
            logging.error("you email may not have been send")
            logging.error(e)
            exit(1)
        self._support_tls = False
        self._tls_conf_func = None
        self._ready = False

    def use_custom_tls(self, func):
        self._tls_conf_func = func
        return self

    def authentication(self, username, passwd, initial_response_ok):
        try:
            self._client.login(username, passwd, initial_response_ok=initial_response_ok)
        except smtplib.SMTPException as e:
            logging.error("Authentication failed", exc_info=e)
            exit(1)

    def send_email(self, em: Email) -> Dict[str, Tuple[int, bytes]]:
        if not self._ready:
            self.ready()
        return self._client.sendmail(
            from_addr=em[EmailStruct.FROM],
            to_addrs=em[EmailStruct.TO],
            msg=em.to_message()
        )

    def ready(self):
        # step 1: check server support EHLO or HELO
        if not self.ping():
            logging.error("Remote server do not support `HELO` or `EHLO`, exit process")
            exit(1)
        # step 2:  does remote server support tls ?
        if self.enable_tls_if_need():
            # server support trying send EHLO
            if not self.tls_ping():
                logging.error("Remote server create tls connection failed, exit process")
                exit(1)
        else:
            logging.info("connection not base on tls")
        # step 3: ready to send email
        self._ready = True

    @staticmethod
    def __enable_tls():
        tls = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        tls.set_default_verify_paths()
        tls.verify_mode = ssl.CERT_REQUIRED
        return tls

    @staticmethod
    def _check_tls(tls):
        if not tls:
            logging.error("tls function return `None` when use user custom function")
            return False
        return True

    def enable_tls_if_need(self):
        if self._support_tls:
            if self._tls_conf_func:
                tls = self._tls_conf_func()
            else:
                tls = self.__enable_tls()
            self._client.starttls(context=tls if self._check_tls(tls) else self.__enable_tls())
            return True
        return False

    def tls_ping(self):
        code = self._client.ehlo()[0]
        if not (200 <= code <= 299):
            logging.error("Could't `EHLO` after `STARTTLS`")
            return False
        logging.info("Enable TlS Connection")
        return True

    def ping(self):
        code = self._client.ehlo()[0]
        use_estmp = (200 <= code <= 299)
        if not use_estmp:
            logging.info("Remote server do not support `EHLO` trying use `HELO`")
            code = self._client.helo()[0]
            if not (200 <= code <= 299):
                logging.error("Remote server refused `HELO`,code: ", code)
                return False
        else:
            if self._client.has_extn("starttls"):
                self._support_tls = True

        return True

    def close(self):
        self._client.quit()


@WithContext
class POP3Sender:
    pass


@WithContext
class IMAPSender:
    pass
