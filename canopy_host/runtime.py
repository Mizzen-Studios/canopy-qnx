"""Bounded Linux SocketCAN processes; host simulation, never QNX evidence."""
import argparse
import json
import math
import os
import time
from pathlib import Path
from .protocol import HEARTBEAT_ID
from .safety import Actuator, Inputs, Safestop
from .socketcan import SocketCAN

SOURCE = 'HOST VCAN live SocketCAN; simulated vehicle; NOT QNX'


def emit(stream, event, **values):
    record = dict(schema='canopy.host-runtime.v1', source=SOURCE,
                  monotonic_ns=time.monotonic_ns(), pid=os.getpid(), event=event,
                  **values)
    stream.write(json.dumps(record, allow_nan=False, sort_keys=True) + '\n')
    stream.flush()


def load_inputs(path, now_ns):
    """Atomic local snapshot; missing/malformed/future timestamps fail closed.

    Ages derive from CLOCK_MONOTONIC. No pilot latch/clear field exists.
    This local test input is not an authenticated sensor trust boundary.
    """
    try:
        data = json.loads(Path(path).read_text())
        if not isinstance(data, dict):
            raise ValueError('snapshot must be object')
        stamp = data['monotonic_ns']
        if type(stamp) is not int or not 0 <= stamp <= now_ns:
            raise ValueError('invalid timestamp')
        age = (now_ns - stamp) // 1_000_000
        obstacle, pilot = float(data['obstacle_m']), float(data['pilot_speed_mps'])
        if not math.isfinite(obstacle) or not math.isfinite(pilot):
            raise ValueError('nonfinite sensor')
        return Inputs(speed_age_ms=age, obstacle_age_ms=age,
                      obstacle_m=obstacle, pilot_speed_mps=pilot)
    except (OSError, ValueError, KeyError, TypeError, OverflowError):
        return Inputs(speed_age_ms=31, obstacle_age_ms=31)


def sender(interface, duration, output, inputs, fault_file=None):
    stop = Safestop()
    bus = SocketCAN(interface, timeout=0.002)
    end = time.monotonic() + duration
    previous = None
    frozen = None
    try:
        with open(output, 'w') as stream:
            emit(stream, 'ready', role='safestop-sender', interface=interface)
            while time.monotonic() < end:
                begin = time.monotonic_ns()
                now_ms = begin // 1_000_000
                if previous is not None and now_ms <= previous:
                    time.sleep(0.001)
                    continue
                previous = now_ms
                snapshot = load_inputs(inputs, begin)
                packet = stop.cycle(now_ms, snapshot)
                payload = packet.encode()
                mode = ''
                if fault_file:
                    try:
                        mode = Path(fault_file).read_text().strip()
                    except OSError:
                        pass
                if mode == 'frozen' and frozen is not None:
                    payload = frozen
                elif mode == 'bad-crc':
                    payload = payload[:-1] + bytes([payload[-1] ^ 1])
                else:
                    frozen = payload
                bus.send(HEARTBEAT_ID, payload)
                emit(stream, 'heartbeat', state=packet.state.name, brake=packet.brake,
                     counter=packet.counter, payload_hex=payload.hex(), fault=mode,
                     latched=stop.latched, fresh_cycles=stop.fresh_cycles,
                     sensor_age_ms=snapshot.speed_age_ms)
                time.sleep(max(0, 0.01 - (time.monotonic_ns() - begin) / 1e9))
    finally:
        bus.close()


def actuator(interface, duration, output, initial_speed=10.0):
    ecu = Actuator(initial_speed)
    ecu.now_ms = time.monotonic_ns() // 1_000_000
    bus = SocketCAN(interface, timeout=0.002)
    end = time.monotonic() + duration
    try:
        with open(output, 'w') as stream:
            emit(stream, 'ready', role='actuator-ecu', interface=interface,
                 vehicle_source='host simulated longitudinal model, 4 m/s^2 full brake')
            last_sample = 0
            while time.monotonic() < end:
                frame = None
                try:
                    frame = bus.receive()
                except ValueError:
                    emit(stream, 'invalid-transport-frame')
                now_ms = time.monotonic_ns() // 1_000_000
                before = ecu.timeout
                accepted = None
                if frame is not None:
                    if frame[0] == HEARTBEAT_ID:
                        accepted = ecu.receive(now_ms, *frame)
                    else:
                        ecu.advance(now_ms)
                else:
                    ecu.advance(now_ms)
                if before != ecu.timeout:
                    emit(stream, 'watchdog-transition', watchdog=ecu.timeout,
                         last_valid_ms=ecu.last_valid_ms, observed_ms=now_ms,
                         elapsed_since_valid_ms=(now_ms - ecu.last_valid_ms
                                                if ecu.last_valid_ms is not None else None))
                if frame is not None or now_ms - last_sample >= 20:
                    emit(stream, 'actuator', time_ms=now_ms, speed_mps=ecu.speed_mps,
                         brake=ecu.brake, hazards=ecu.hazards, watchdog=ecu.timeout,
                         last_valid_ms=ecu.last_valid_ms, accepted=accepted,
                         rejected=ecu.rejected, recovery_cycles=ecu.recovery_cycles,
                         received_hex=frame[1].hex() if frame else None)
                    last_sample = now_ms
    finally:
        bus.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('role', choices=['sender', 'actuator'])
    parser.add_argument('--interface', default='vcan0')
    parser.add_argument('--duration', type=float, default=8)
    parser.add_argument('--output', required=True)
    parser.add_argument('--inputs')
    parser.add_argument('--fault-file')
    args = parser.parse_args()
    if not math.isfinite(args.duration) or not 0 < args.duration <= 60:
        parser.error('duration must be finite in (0, 60] seconds')
    if args.role == 'sender':
        if not args.inputs:
            parser.error('sender requires --inputs')
        sender(args.interface, args.duration, args.output, args.inputs, args.fault_file)
    else:
        actuator(args.interface, args.duration, args.output)


if __name__ == '__main__':
    main()
