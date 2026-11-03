"""Project-owned demo CAN mapping; not an OEM DBC or running QPP connector."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable

SPEED = 'Vehicle.Speed'
STEERING = 'Vehicle.Chassis.SteeringWheel.Angle'
DISTANCE = 'Vehicle.ADAS.ObstacleDetection.Front.Distance'


@dataclass(frozen=True)
class Signal:
    path: str
    can_id: int
    byteorder: str
    signed: bool
    scale: Decimal
    minimum: Decimal
    maximum: Decimal
    unit: str
    datatype: str


SIGNALS = (
    Signal(SPEED, 0x100, 'little', False, Decimal('.01'), Decimal('0'),
           Decimal('250'), 'km/h', 'float'),
    Signal(STEERING, 0x101, 'big', True, Decimal('1'), Decimal('-720'),
           Decimal('720'), 'degrees', 'int16'),
    Signal(DISTANCE, 0x102, 'big', False, Decimal('.01'), Decimal('0'),
           Decimal('500'), 'm', 'float'),
)
_BY_ID = {s.can_id: s for s in SIGNALS}
_BY_PATH = {s.path: s for s in SIGNALS}


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError('expected a finite numeric value')
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('invalid number') from exc
    if not number.is_finite():
        raise ValueError('expected a finite numeric value')
    return number


def encode(path: str, value) -> tuple[int, bytes]:
    """Encode an exactly representable physical value; never round or clamp."""
    if not isinstance(path, str) or path not in _BY_PATH:
        raise ValueError('unknown signal path')
    signal = _BY_PATH[path]
    number = _number(value)
    if not signal.minimum <= number <= signal.maximum:
        raise ValueError('signal outside project demo range')
    # Integer ratios prevent Decimal context precision from silently rounding.
    numerator, denominator = number.as_integer_ratio()
    scale_num, scale_den = signal.scale.as_integer_ratio()
    raw, remainder = divmod(numerator * scale_den, denominator * scale_num)
    if remainder:
        raise ValueError('value not exactly representable')
    return signal.can_id, raw.to_bytes(2, signal.byteorder, signed=signal.signed)


def decode(can_id: int, payload: bytes) -> tuple[str, Decimal]:
    """Bare standard SocketCAN ID only (flags rejected), exact DLC=2."""
    if type(can_id) is not int or can_id not in _BY_ID:
        raise ValueError('unknown ID or unsupported CAN flags')
    if type(payload) is not bytes or len(payload) != 2:
        raise ValueError('expected two immutable classic CAN data bytes')
    signal = _BY_ID[can_id]
    raw = int.from_bytes(payload, signal.byteorder, signed=signal.signed)
    value = Decimal((int(raw < 0), tuple(map(int, str(abs(raw)))),
                     signal.scale.as_tuple().exponent))
    if not signal.minimum <= value <= signal.maximum:
        raise ValueError('signal outside project demo range')
    return signal.path, value


@dataclass(frozen=True)
class Update:
    path: str
    value: Decimal
    unit: str
    source: str
    received_ns: int


@dataclass(frozen=True)
class TextWrite:
    """Intent only: constructing this object never opens a QPP service."""
    filename: str
    payload: bytes
    update: Update


def _provenance(source, received_ns):
    if (not isinstance(source, str) or not source.strip() or
            len(source) > 160 or any(ord(c) < 32 or ord(c) == 127 for c in source)):
        raise ValueError('a printable source tag is required')
    if type(received_ns) is not int or received_ns < 0:
        raise ValueError('a nonnegative monotonic reception time is required')


def qpp_text_write(update: Update, mount: str = '/dev/signal') -> TextWrite:
    """Allowlisted POSIX text intent matching pinned upstream semantics."""
    if not isinstance(update, Update):
        raise ValueError('expected an Update')
    encode(update.path, update.value)
    signal = _BY_PATH[update.path]
    _provenance(update.source, update.received_ns)
    if update.unit != signal.unit:
        raise ValueError('unit mismatch')
    if (not isinstance(mount, str) or not mount.startswith('/') or
            any(part in ('', '.', '..') for part in mount.split('/')[1:]) or
            any(c in mount for c in '?\x00\n\r')):
        raise ValueError('expected a normalized absolute mount path')
    value = _number(update.value)
    text = str(int(value)) if signal.datatype == 'int16' else format(value, 'f')
    return TextWrite(mount + '/' + update.path.replace('.', '/') + '?text',
                     text.encode('ascii') + b'\0', update)


class HostAdapter:
    """Injectable host-only sink; not a QPP plugin or device reader.

    Validation precedes sink invocation; failures propagate, never refresh or
    retry stale values. Source is caller-supplied, not authenticated.
    """

    def __init__(self, sink: Callable[[Update], None]):
        if not callable(sink):
            raise ValueError('sink must be callable')
        self._sink = sink

    def receive(self, can_id: int, payload: bytes, *, source: str,
                received_ns: int, is_fd: bool = False) -> Update:
        _provenance(source, received_ns)
        if type(is_fd) is not bool or is_fd:
            raise ValueError('CAN FD is unsupported')
        path, value = decode(can_id, payload)
        update = Update(path, value, _BY_PATH[path].unit, source, received_ns)
        self._sink(update)
        return update
