import struct
import time
from enum import Enum

from app.connector import BasicConnector
from app.exceptions import InvalidCommandError, InvalidChecksumError, DeviceAuthError, InvalidResponseError, \
    ReadFailedError, AdbCommandFailureException, InterleavedDataError

# Maximum amount of data in an ADB packet.
MAX_ADB_DATA = 4096
# ADB protocol version.
VERSION = 0x01000000

TIMEOUT_CODE = -7


class Auth(Enum):
    TOKEN = 1
    SIGNATURE = 2
    RSA_PUBLIC_KEY = 3


class DataCommand(Enum):
    SYNC = b'SYNC'
    CNXN = b'CNXN'
    AUTH = b'AUTH'
    OPEN = b'OPEN'
    OKAY = b'OKAY'
    CLOSE = b'CLSE'
    WRITE = b'WRTE'
    FAIL = b'FAIL'

    @classmethod
    def get_all_command(cls):
        return [[k for k, v in va.items()] for attr, va in cls.__dict__.items() if attr == "_value2member_map_"][0]


class AndroidDebugBridgeProtocol:

    def __init__(self, connector, local_id, remote_id, timeout_ms):
        self.connector = connector
        self.local_id = local_id
        self.remote_id = remote_id
        self.timeout_ms = timeout_ms

    def __send(self, command, arg0, arg1, data=b''):
        message = AndroidDebugBridgeMessage(command, arg0, arg1, data)
        message.send_packed_message(self.connector, self.timeout_ms)

    def write(self, data):
        self.__send(DataCommand.WRITE.value, arg0=self.local_id, arg1=self.remote_id, data=data)
        cmd, okay_data = self.read_until_cmd_is(DataCommand.OKAY)
        if cmd != DataCommand.OKAY.value:
            if cmd == DataCommand.FAIL.value:
                raise AdbCommandFailureException(
                    'Command failed.', okay_data)
            raise InvalidCommandError(
                'Expected an OKAY in response to a WRITE, got %s (%s)',
                cmd, okay_data)
        return len(data)

    def read_until_conn_close(self):
        while True:
            cmd, data = self.read_until_cmd_is(DataCommand.CLOSE, DataCommand.WRITE)
            if cmd == DataCommand.CLOSE.value:
                self.__send(DataCommand.CLOSE.value, arg0=self.local_id, arg1=self.remote_id)
                break
            if cmd != DataCommand.WRITE.value:
                if cmd == DataCommand.FAIL.value:
                    raise AdbCommandFailureException(
                        'Command failed.', data)
                raise InvalidCommandError('Expected a WRITE or a CLOSE, got %s (%s)',
                                          cmd, data)
            yield data

    def send_ok(self):
        self.__send(DataCommand.OKAY.value, arg0=self.local_id, arg1=self.remote_id)

    def read_until_cmd_is(self, *command: DataCommand):
        cmd, remote_id, local_id, data = AndroidDebugBridgeMessage.read_from_connector(
            self.connector, [cmd.value for cmd in command], self.timeout_ms)
        if local_id != 0 and self.local_id != local_id:
            raise InterleavedDataError("We don't support multiple streams...")
        if remote_id != 0 and self.remote_id != remote_id:
            raise InvalidResponseError(
                'Incorrect remote id, expected %s got %s' % (
                    self.remote_id, remote_id))
        # Ack write packets.
        if cmd == DataCommand.WRITE.value:
            self.send_ok()
        return cmd, data

    def close(self):
        self.__send(DataCommand.CLOSE.value, arg0=self.local_id, arg1=self.remote_id)
        cmd, data = self.read_until_cmd_is(DataCommand.CLOSE)
        if cmd != DataCommand.CLOSE.value:
            if cmd == DataCommand.FAIL.value:
                raise AdbCommandFailureException('Command failed.', data)
            raise InvalidCommandError(f'Expected a {DataCommand.CLOSE} response, got %s (%s)',
                                      cmd, data)


def make_command():
    id_to_wire = {
        cmd_id: sum(c << (i * 8) for i, c in enumerate(bytearray(cmd_id))) for cmd_id in DataCommand.get_all_command()
    }
    wire_to_id = {wire: cmd_id for cmd_id, wire in id_to_wire.items()}
    return id_to_wire, wire_to_id


class AndroidDebugBridgeMessage:
    _PACK_FORMAT_ = b'<6I'

    commands, constants = make_command()

    def __init__(self, command=None, arg0=None, arg1=None, data=b''):
        self.command = self.commands[command]
        self.magic = self.command ^ 0xFFFFFFFF
        self.arg0 = arg0
        self.arg1 = arg1
        self.data = data

    @staticmethod
    def calc_check_sum(data):
        # adb中的检验和为所有直接加起来形成的整数（据说）
        if isinstance(data, bytearray):
            total = sum(data)
        elif isinstance(data, bytes):
            total = sum(data)
        else:
            # Unicode字符
            total = sum(map(ord, data))
        return total & 0xFFFFFFFF

    @property
    def checksum(self):
        return self.calc_check_sum(self.data)

    def pack(self):
        return struct.pack(self._PACK_FORMAT_, self.command, self.arg0, self.arg1,
                           len(self.data), self.checksum, self.magic)

    @classmethod
    def unpack(cls, message):
        try:
            cmd, arg0, arg1, data_length, data_checksum, unused_magic = struct.unpack(
                cls._PACK_FORMAT_, message)
        except struct.error as e:
            raise ValueError('Unable to unpack ADB command.', cls._PACK_FORMAT_, message, e)
        return cmd, arg0, arg1, data_length, data_checksum

    def send_packed_message(self, conn: BasicConnector, timeout=None):
        conn.write(self.pack(), timeout)
        conn.write(self.data, timeout)

    @classmethod
    def read_from_connector(cls, conn: BasicConnector, expected_cmds, timeout_ms=None, total_timeout_ms=None):
        total_timeout_ms = conn.timeout_second(total_timeout_ms)
        start = time.time()
        while True:
            msg = conn.read(24, timeout_ms)
            cmd, arg0, arg1, data_length, data_checksum = cls.unpack(msg)
            command = cls.constants.get(cmd)
            if not command:
                raise InvalidCommandError(
                    'Unknown command: %x' % cmd, cmd, (arg0, arg1))
            if command in expected_cmds:
                break

            if time.time() - start > total_timeout_ms:
                raise InvalidCommandError(
                    'Never got one of the expected responses (%s)' % expected_cmds,
                    cmd, (timeout_ms, total_timeout_ms))

        if data_length > 0:
            data = bytearray()
            while data_length > 0:
                temp = conn.read(data_length, timeout_ms)
                if len(temp) != data_length:
                    print(
                        "Data_length {} does not match actual number of bytes read: {}".format(data_length, len(temp)))
                data += temp

                data_length -= len(temp)

            actual_checksum = cls.calc_check_sum(data)
            if actual_checksum != data_checksum:
                raise InvalidChecksumError(
                    'Received checksum %s != %s', (actual_checksum, data_checksum))
        else:
            data = b''
        return command, arg0, arg1, bytes(data)

    @classmethod
    def Connect(cls, conn, banner=b'notadb', rsa_keys=None, auth_timeout_ms=100):
        msg = cls(
            command=DataCommand.CNXN.value, arg0=VERSION, arg1=MAX_ADB_DATA,
            data=b'host::%s\0' % banner)
        msg.send_packed_message(conn)
        cmd, arg0, arg1, banner = cls.read_from_connector(conn, [b'CNXN', b'AUTH'])
        if cmd == DataCommand.AUTH.value:
            if not rsa_keys:
                raise DeviceAuthError(
                    'Device authentication required, no keys available.')
            for rsa_key in rsa_keys:
                if arg0 != Auth.TOKEN.value:
                    raise InvalidResponseError(
                        'Unknown AUTH response: %s %s %s' % (arg0, arg1, banner))
                signed_token = rsa_key.Sign(banner)
                msg = cls(
                    command=DataCommand.AUTH.value, arg0=Auth.SIGNATURE.value, arg1=0, data=signed_token)
                msg.send_packed_message(conn)
                cmd, arg0, unused_arg1, banner = cls.read_from_connector(conn, [DataCommand.CNXN.value,
                                                                                DataCommand.AUTH.value])
                if cmd == DataCommand.CNXN.value:
                    return banner
            msg = cls(
                command=DataCommand.AUTH.value, arg0=Auth.RSA_PUBLIC_KEY.valu, arg1=0,
                data=rsa_keys[0].GetPublicKey() + b'\0')
            msg.send_packed_message(conn)
            try:
                cmd, arg0, unused_arg1, banner = cls.read_from_connector(
                    conn, [DataCommand.CNXN.value], timeout_ms=auth_timeout_ms)
            except ReadFailedError as e:
                if e.usb_error.value == TIMEOUT_CODE:  # Timeout
                    raise DeviceAuthError(
                        'Accept auth key on device, then retry.')
                raise
            return banner
        return banner

    @classmethod
    def open_connection(cls, conn, destination, timeout_ms=None):
        local_id = 1
        msg = cls(
            command=DataCommand.OPEN.value, arg0=local_id, arg1=0,
            data=destination + b'\0')
        msg.send_packed_message(conn, timeout_ms)
        cmd, remote_id, their_local_id, _ = cls.read_from_connector(conn,
                                                                    [DataCommand.CLOSE.value, DataCommand.OKAY.value],
                                                                    timeout_ms=timeout_ms)
        if local_id != their_local_id:
            raise InvalidResponseError(
                'Expected the local_id to be {}, got {}'.format(local_id, their_local_id))
        if cmd == DataCommand.CLOSE.value:
            cmd, remote_id, their_local_id, _ = cls.read_from_connector(conn,
                                                                        [DataCommand.CLOSE.value,
                                                                         DataCommand.OKAY.value],
                                                                        timeout_ms=timeout_ms)
            if cmd == DataCommand.CLOSE.value:
                return None
        if cmd != DataCommand.OKAY.value:
            raise InvalidCommandError('Expected a ready response, got {}'.format(cmd),
                                      cmd, (remote_id, their_local_id))
        return AndroidDebugBridgeProtocol(conn, local_id, remote_id, timeout_ms)

    @classmethod
    def streaming_command(cls, usb, service, command='', timeout_ms=None):
        if not isinstance(command, bytes):
            command = command.encode('utf8')
        connection = cls.open_connection(
            usb, destination=b'%s:%s' % (service, command),
            timeout_ms=timeout_ms)
        for data in connection.ReadUntilClose():
            yield data.decode('utf8')


if __name__ == '__main__':
    print(DataCommand.get_all_command())
