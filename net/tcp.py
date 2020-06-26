import socket
from enum import Enum


class MsgFlag(Enum):
    # 告诉内核，目标主机在本地网络，不用查路由表
    MSG_DONTROUTE = socket.MSG_DONTROUTE
    # 将单个I／O操作设置为非阻塞模式
    MSG_DONTWAIT = socket.MSG_DONTWAIT
    # 指明发送的是带外信息
    MSG_OOB = socket.MSG_OOB
    # 可以查看可读的信息，在接收数据后不会将这些数据丢失
    MSG_PEEK = socket.MSG_PEEK
    # 通知内核直到读到请求的数据字节数时，才返回
    MSG_WAITALL = socket.MSG_WAITALL


class SockLevel(Enum):
    # 如果想要在套接字级别上设置选项，就必须把level设置为SOL_SOCKET
    SOL_SOCKET = socket.SOL_SOCKET
    IPPROTO_TCP = socket.IPPROTO_TCP


class SockOpt(Enum):
    # 允许套接口传送广播信息
    # 只有数据报套接字支持广播，并且还必须是在支持广播消息的网络上
    SO_BROADCAST = socket.SO_BROADCAST
    # 记录调试信息
    SO_DEBUG = socket.SO_DEBUG
    # 禁止选径；直接传送
    SO_DONTROUTE = socket.SO_DONTROUTE
    # 发送“保持活动”包
    SO_KEEPALIVE = socket.SO_KEEPALIVE
    # 如关闭时有未发送数据，则逗留
    SO_LINGER = socket.SO_LINGER
    # 在常规数据流中接收带外数据。
    SO_OOBINLINE = socket.SO_OOBINLINE
    # 为接收确定缓冲区大小
    SO_RCVBUF = socket.SO_RCVBUF
    # 允许套接口和一个已在使用中的地址捆绑
    # 默认情况下，当监听服务器在步骤d通过调用socket，bind和listen重新启动时，
    # 由于他试图捆绑一个现有连接（即正由早先派生的那个子进程处理着的连接）上的端口，
    # 从而bind调用会失败
    SO_REUSEADDR = socket.SO_REUSEADDR
    # 指定发送缓冲区大小
    SO_SNDBUF = socket.SO_SNDBUF
    # 禁止发送合并的Nagle算法。
    TCP_NODELAY = socket.TCP_NODELAY


class TcpStream:

    def __init__(self, sock: socket.socket, addr):
        self._sock = sock
        self._addr = addr

    def write_all(self, data):
        # C语言实现，在发送循环中会释放GIL，python其他线程在发生数据完成前不会竞争资源
        # byte_count = 0
        # while byte_count < len(message):
        #   message_remaining = message[byte_send:]
        #   byte_sent += sock.send(message_remaining)
        self._sock.sendall(data)

    def write(self, data, flags: MsgFlag) -> int:
        # 在发送数据时会碰到以下3种情况
        # 1. 网卡正好空闲，缓冲区未满，send会立即返回的是整个数据的长度
        # 2. 网卡正忙，缓冲区已满，系统不愿分配更多空间，send会阻塞进程暂停应用，知道本地网络栈能够接收并发送数据
        # 3. 发送缓冲区快满了，但有一定空间，发生的部分数据进入发送缓冲区等待发送，剩余数据必须等待，send会返回发送的部分数据长度
        return self._sock.send(data, flags.value if flags else 0)

    def read(self, buff_len, flags: MsgFlag) -> bytes:
        return self._sock.recv(buff_len, flags.value if flags else 0)

    def read_len(self, length, flags: MsgFlag) -> bytes:
        data = b''
        while len(data) < length:
            more = self._sock.recv(length - len(data), flags.value if flags else 0)
            if not more:
                raise EOFError(
                    f"was except {length} bytes buf only received {len(data)} bytes before the socket closed")
            data += more
        return data

    @classmethod
    def connect(cls, ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        return cls(sock, ip)


class TcpListener:

    def __init__(self, addr: str, ip: int):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TCP_NODELAY选项禁止Nagle算法
        # Nagle算法通过将未确认的数据存入缓冲区直到蓄足一个包一起发送的方法，来减少主机发送的零碎小数据包的数目
        # TCP_NODELAY是唯一使用IPPROTO_TCP层的选项，其他所有选项都使用SOL_SOCKET层
        # 应用程序认为某个TCO链接关闭了，网络栈会在一个等待状态中将该记录保持4分钟，RFC称为CLOSE-WAIT和TIME-WAIT
        self._sock.setsockopt(SockLevel.SOL_SOCKET.value, SockOpt.SO_REUSEADDR.value, int(True))
        self._sock.bind((addr, ip))

    def incoming(self, handle):
        sock, addr = self._sock.accept()
        while True:
            handle(TcpStream(sock, addr))
