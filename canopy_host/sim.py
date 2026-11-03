"""Logical-time fixture, not measured telemetry or a QNX execution."""
import argparse
import json
import random
from .protocol import HEARTBEAT_ID
from .safety import Actuator, Inputs, Safestop


def simulate(scenario='drop', seed=7):
    if scenario not in ('drop', 'bad-crc', 'frozen', 'obstacle', 'stale', 'pilot'):
        raise ValueError('unknown scenario')
    rng = random.Random(seed)
    ecu, stop = Actuator(8 + rng.randrange(3)), Safestop()
    frozen = None
    records = []
    for now in range(0, 4001, 10):
        fault = 500 <= now < 3500
        inputs = Inputs(obstacle_m=1 if fault and scenario == 'obstacle' else 100,
                        speed_age_ms=40 if fault and scenario == 'stale' else 0,
                        pilot_speed_mps=30 if fault and scenario == 'pilot' else 10)
        packet = stop.cycle(now, inputs).encode()
        if now == 490:
            frozen = packet
        if fault and scenario == 'frozen':
            packet = frozen
        if fault and scenario == 'bad-crc':
            packet = packet[:-1] + bytes([packet[-1] ^ 1])
        accepted = False
        if not (fault and scenario == 'drop'):
            accepted = ecu.receive(now, HEARTBEAT_ID, packet)
        else:
            ecu.advance(now)
        records.append(dict(source='host deterministic simulation; NOT QNX',
                            scenario=scenario, seed=seed, time_ms=now,
                            speed_mps=round(ecu.speed_mps, 6), brake=ecu.brake,
                            hazards=ecu.hazards, watchdog=ecu.timeout,
                            safestop=stop.latched, accepted=accepted))
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', default='drop',
                        choices=['drop', 'bad-crc', 'frozen', 'obstacle', 'stale', 'pilot'])
    parser.add_argument('--seed', type=int, default=7)
    args = parser.parse_args()
    for record in simulate(args.scenario, args.seed):
        print(json.dumps(record, sort_keys=True))


if __name__ == '__main__':
    main()
