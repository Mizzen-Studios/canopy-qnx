"""Integrated Linux vcan session; synthetic sensors/vehicle, never QNX."""
import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from .pilot import Pilot
from .runtime import SOURCE, emit
from .socketcan import SocketCAN
from .vss import HostAdapter, SPEED, STEERING, DISTANCE, encode


class RotatingLog:
    """Bound disk use with three retained backup segments."""
    def __init__(self, path, limit=1_000_000, backups=3):
        self.path, self.limit, self.backups = Path(path), limit, backups
        self.stream = self.path.open('w')

    def write(self, text):
        if self.stream.tell() + len(text.encode()) > self.limit:
            self.stream.close()
            for i in range(self.backups, 0, -1):
                old = self.path if i == 1 else Path(str(self.path) + f'.{i-1}')
                if old.exists():
                    old.replace(Path(str(self.path) + f'.{i}'))
            self.stream = self.path.open('w')
        return self.stream.write(text)

    def flush(self):
        self.stream.flush()

    def close(self):
        self.stream.close()


def run(directory, interface='vcan0', duration=10, obstacle=100):
    if duration is not None and (not math.isfinite(duration) or not 0 < duration <= 3600):
        raise ValueError('duration must be in (0, 3600] seconds')
    if not math.isfinite(obstacle) or not 0 <= obstacle <= 100:
        raise ValueError('obstacle must be in [0, 100] metres')
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    children, handles = [], []
    bus = None
    stopping = False
    def stop(*_):
        nonlocal stopping
        stopping = True
    old_handlers = {s: signal.signal(s, stop) for s in (signal.SIGTERM, signal.SIGINT)}
    log = RotatingLog(directory / 'session.jsonl')
    try:
        (directory / 'session.pid').write_text(str(os.getpid()) + chr(10))
        bus = SocketCAN(interface, timeout=0.001)
        # A separate sender socket makes looped-back sensor reception real.
        sensors = SocketCAN(interface, timeout=0.001)
        pilot = Pilot()
        updates = {}
        adapter = HostAdapter(lambda u: updates.__setitem__(u.path, u))
        inputs = directory / 'inputs.json'
        inputs.write_text(json.dumps(dict(monotonic_ns=time.monotonic_ns(), obstacle_m=obstacle,
                                          pilot_speed_mps=0, source=SOURCE)))
        for role in ('actuator', 'sender'):
            error = (directory / (role + '.stderr')).open('w')
            handles.append(error)
            command = [sys.executable, '-m', 'canopy_host.runtime', role, '--interface', interface,
                       '--long-running', '--rotate-bytes', '1000000',
                       '--output', str(directory / (role + '.jsonl'))]
            if role == 'sender':
                command += ['--inputs', str(inputs)]
            child = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=error)
            children.append(child)
            emit(log, 'child-start', role=role, child_pid=child.pid)
            if role == 'actuator':
                deadline = time.monotonic() + 2
                ready = directory / 'actuator.jsonl'
                while not ready.exists() or ready.stat().st_size == 0:
                    if child.poll() is not None or time.monotonic() >= deadline:
                        raise RuntimeError('actuator readiness failed')
                    time.sleep(.002)
        start = time.monotonic()
        next_sensor, next_agent = start, start
        sequence = 0
        while not stopping and (duration is None or time.monotonic() - start < duration):
            if any(p.poll() is not None for p in children):
                raise RuntimeError('host runtime child exited; see role stderr')
            now = time.monotonic()
            if now >= next_sensor:
                # Explicit synthetic 36 km/h sensor, not simulated ECU feedback.
                for path, value in ((SPEED, 36), (STEERING, 0), (DISTANCE, round(obstacle, 2))):
                    sensors.send(*encode(path, value))
                next_sensor = now + .01
            frame = bus.receive()
            if frame and frame[0] in (0x100, 0x101, 0x102):
                u = adapter.receive(*frame, source=SOURCE, received_ns=time.monotonic_ns())
                emit(log, 'vss-update', path=u.path, value=float(u.value), unit=u.unit,
                     received_ns=u.received_ns, can_id=frame[0], payload_hex=frame[1].hex())
            if len(updates) == 3:
                stamp = min(u.received_ns for u in updates.values())
                request = pilot.request(int(updates[DISTANCE].value * 100),
                                        int(updates[SPEED].value * 1000 / 36), 0)
                snapshot = dict(monotonic_ns=stamp, obstacle_m=float(updates[DISTANCE].value),
                                pilot_speed_mps=request.speed_mps, steering_deg=request.steering_deg,
                                source=SOURCE)
                temporary = directory / 'inputs.new'
                temporary.write_text(json.dumps(snapshot))
                temporary.replace(inputs)
                if now >= next_agent:
                    emit(log, 'host-agent', sequence=sequence, interface=interface,
                         sender_pid=children[1].pid, actuator_pid=children[0].pid,
                         sensor_source='synthetic project VSS frames via kernel SocketCAN',
                         pilot_source='learned host decision tree; request only', inputs=snapshot,
                         vss={k: float(v.value) for k, v in updates.items()})
                    sequence += 1
                    next_agent = now + .05
        return directory
    finally:
        for p in children:
            if p.poll() is None:
                p.terminate()
        for p in children:
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait(timeout=3)
        for h in handles:
            h.close()
        if bus:
            bus.close()
        if 'sensors' in locals():
            sensors.close()
        emit(log, 'cleanup', child_returncodes=[p.returncode for p in children])
        log.close()
        (directory / 'session.pid').unlink(missing_ok=True)
        for s, handler in old_handlers.items():
            signal.signal(s, handler)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, help='new directory; never overwrite evidence')
    p.add_argument('--interface', default='vcan0')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--duration', type=float, default=10)
    mode.add_argument('--long-running', action='store_true')
    p.add_argument('--obstacle', type=float, default=100)
    a = p.parse_args(argv)
    try:
        run(a.output, a.interface, None if a.long_running else a.duration, a.obstacle)
    except (ValueError, OSError, RuntimeError) as e:
        p.error(str(e))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
