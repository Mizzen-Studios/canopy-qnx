"""Classic CAN 0x200, four bytes: state, brake %, ctr4, CRC.

CRC-8/SAE-J1850 parameters: poly=0x1d init=0xff xorout=0xff,
non-reflected. CRC covers the fixed ID (02 00) followed by bytes 0..2.
This is E2E-style error detection, NOT AUTOSAR conformance or authentication.
"""
from dataclasses import dataclass
from enum import IntEnum

HEARTBEAT_ID = 0x200


class State(IntEnum):
    DRIVE = 0
    BRAKE = 1
    SAFE_STOP = 2
    RECOVER = 3


def crc8(data: bytes) -> int:
    crc = 0xff
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ (0x1d if crc & 0x80 else 0)) & 0xff
    return crc ^ 0xff


@dataclass(frozen=True)
class Heartbeat:
    state: State
    brake: int
    counter: int

    def encode(self) -> bytes:
        if not isinstance(self.state, State):
            raise ValueError('invalid state')
        if type(self.brake) is not int or not 0 <= self.brake <= 100:
            raise ValueError('brake outside 0..100')
        if type(self.counter) is not int or not 0 <= self.counter <= 15:
            raise ValueError('counter outside 0..15')
        if self.state == State.SAFE_STOP and self.brake != 100:
            raise ValueError('SAFE_STOP requires full brake')
        body = bytes((self.state, self.brake, self.counter))
        return body + bytes((crc8(b'\x02\x00' + body),))

    @classmethod
    def decode(cls, can_id: int, payload: bytes):
        if can_id != HEARTBEAT_ID or len(payload) != 4:
            raise ValueError('wrong ID or length')
        if crc8(b'\x02\x00' + payload[:3]) != payload[3]:
            raise ValueError('bad CRC')
        value = cls(State(payload[0]), payload[1], payload[2])
        value.encode()  # range and reserved-bit validation
        return value
