"""Optional Linux classic SocketCAN adapter. Never creates interfaces.

Caller must schedule Actuator.advance with monotonic time even if receive is
silent; this adapter is transport only, not a watchdog service.
"""
import socket
import struct

FRAME = struct.Struct('=IB3x8s')


def pack(can_id, payload):
    if not 0 <= can_id <= 0x7ff or len(payload) > 8:
        raise ValueError('classic standard CAN only')
    return FRAME.pack(can_id, len(payload), payload.ljust(8, b'\0'))


def unpack(frame):
    if len(frame) != FRAME.size:
        raise ValueError('wrong CAN frame size')
    can_id, length, payload = FRAME.unpack(frame)
    if can_id > 0x7ff or length > 8:
        raise ValueError('extended, RTR, error or invalid frame')
    return can_id, payload[:length]


class SocketCAN:
    def __init__(self, interface='vcan0', timeout=0.01):
        self.sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        try:
            self.sock.settimeout(timeout)
            self.sock.bind((interface,))
        except BaseException:
            self.sock.close()
            raise

    def send(self, can_id, payload):
        frame = pack(can_id, payload)
        if self.sock.send(frame) != len(frame):
            raise OSError('short CAN send')

    def receive(self):
        try:
            return unpack(self.sock.recv(FRAME.size))
        except TimeoutError:
            return None

    def close(self):
        self.sock.close()
