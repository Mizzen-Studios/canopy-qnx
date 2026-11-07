#!/usr/bin/env python3
"""Host input generator / existing ECU; does NOT launch any guest or claim QNX.

Exclusive test bus required. Sends existing 100/102 demo frames, not pilot-clear.
"""
import argparse
import math
import json
import time
from canopy_host.socketcan import SocketCAN
from canopy_host.vss import encode, SPEED, DISTANCE
from canopy_host.runtime import actuator


def stimulus(interface, duration, scenario, fault_after=2.0, recover_after=5.0, events=None):
    if scenario not in ('healthy', 'stale', 'obstacle', 'pilot', 'malformed'):
        raise ValueError('unknown scenario')
    if not math.isfinite(duration) or not 0 < duration <= 60:
        raise ValueError('bounded duration required')
    with_bus = SocketCAN(interface, timeout=0.002)
    start = time.monotonic()
    marked_fault = marked_restore = False
    def marker(event):
        if events:
            with open(events, 'a') as stream:
                stream.write(json.dumps(dict(scenario='stale-none', event=event,
                                             monotonic_ns=time.monotonic_ns()))+'\n')
    try:
        while (elapsed := time.monotonic() - start) < duration:
            fault = fault_after <= elapsed < recover_after
            if scenario == 'stale' and fault and not marked_fault:
                marker('fault-start'); marked_fault = True
            if scenario == 'stale' and elapsed >= recover_after and not marked_restore:
                marker('sensors-restored'); marked_restore = True
            if not (fault and scenario == 'stale'):
                with_bus.send(*encode(SPEED, 90 if fault and scenario == 'pilot' else 36))
                if fault and scenario == 'malformed':
                    with_bus.send(0x102, b'\x00')
                else:
                    with_bus.send(*encode(DISTANCE, 1 if fault and scenario == 'obstacle' else 100))
            time.sleep(0.01)
    finally:
        with_bus.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('role', choices=['stimulus', 'ecu'])
    p.add_argument('--interface', required=True)
    p.add_argument('--duration', type=float, default=8)
    p.add_argument('--scenario', choices=['healthy','stale','obstacle','pilot','malformed'], default='healthy')
    p.add_argument('--output')
    p.add_argument('--events', help='append timestamped actual stale injection/restore actions')
    a = p.parse_args()
    if not math.isfinite(a.duration) or not 0 < a.duration <= 60:
        p.error('duration must be finite in (0,60]')
    if a.role == 'ecu':
        if not a.output:
            p.error('ecu requires --output')
        actuator(a.interface,a.duration,a.output)
    else:
        stimulus(a.interface,a.duration,a.scenario,events=a.events)

if __name__ == '__main__':
    main()
