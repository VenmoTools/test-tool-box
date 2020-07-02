import socket
import ssl
from ssl import SSLContext

from httpclient.strcutures import WithContext
from net.tcp import TcpStream, SockLevel, SockOpt


def get_default_tls_for_server(cafile) -> SSLContext:
    purpose = ssl.Purpose.CLIENT_AUTH
    tls = ssl.create_default_context(purpose=purpose, cafile=cafile)
    tls.load_default_certs(purpose)
    return tls


def get_default_tls_for_client() -> SSLContext:
    purpose = ssl.Purpose.SERVER_AUTH
    tls = ssl.create_default_context(purpose=purpose)
    tls.load_default_certs(purpose)
    return tls


@WithContext
class TlsStream(TcpStream):
    default_ssl_conf = get_default_tls_for_client()

    @classmethod
    def connect(cls, ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = cls.default_ssl_conf.wrap_socket(sock)
        sock.connect((ip, port))
        return cls(sock, ip)


@WithContext
class TLSTcpServer:

    def __init__(self, context: SSLContext):
        self.context = context
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(SockLevel.SOL_SOCKET.value, SockOpt.SO_REUSEADDR.value, 1)
        self._ssl_sock = self.context.wrap_socket(self._sock, server_side=True)

    def incoming(self, handle, disable_auto_close=False):
        sock, ip = self._ssl_sock.accept()
        while True:
            wrap_sock = self.context.wrap_socket(sock, server_side=False, server_hostname=ip)
            if not disable_auto_close:
                with TlsStream(wrap_sock, ip) as tls_client:
                    handle(tls_client)
            else:
                handle(wrap_sock, ip)
