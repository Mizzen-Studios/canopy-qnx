"""Host-only logical-time hero director. Never launches or impersonates QNX."""
from dataclasses import asdict
import random
from .protocol import HEARTBEAT_ID
from .safety import Actuator, Inputs, Safestop

SOURCE = 'host deterministic simulation; NOT QNX'
SCHEMA = 'canopy.host-run.v1'
EVENTS = ('run-start', 'heartbeat-drop-start', 'heartbeat-drop-end',
          'obstacle-start', 'obstacle-end', 'pilot-veto-start', 'pilot-veto-end',
          'watchdog-held', 'watchdog-released', 'latch-held', 'latch-released',
          'vehicle-stopped', 'run-end')


def hero(seed=7):
    if type(seed) is not int or abs(seed) > 9007199254740991:
        raise ValueError('seed must be a safe integer')
    ecu = Actuator(8 + random.Random(seed).randrange(3))
    stop = Safestop()
    previous = None
    marks = {0:'run-start', 500:'heartbeat-drop-start', 3500:'heartbeat-drop-end',
             4000:'obstacle-start', 4500:'obstacle-end', 5000:'pilot-veto-start',
             5500:'pilot-veto-end', 6000:'run-end'}
    for now in range(0, 6001, 10):
        dropped = 500 <= now < 3500
        inputs = Inputs(speed_age_ms=40 if dropped else 0,
                        obstacle_age_ms=40 if dropped else 0,
                        obstacle_m=1 if 4000 <= now < 4500 else 100,
                        pilot_speed_mps=30 if 5000 <= now < 5500 else 10)
        heartbeat = stop.cycle(now, inputs)
        packet = heartbeat.encode()
        accepted = False
        if dropped:
            ecu.advance(now)
        else:
            accepted = ecu.receive(now, HEARTBEAT_ID, packet)
        events = [marks[now]] if now in marks else []
        row = dict(schema=SCHEMA, source=SOURCE, scenario='hero', seed=seed,
                   sequence=now // 10, time_ms=now, clock='logical-ms',
                   speed_mps=round(ecu.speed_mps, 6), brake=ecu.brake,
                   hazards=ecu.hazards, watchdog=ecu.timeout, safestop=stop.latched,
                   accepted=accepted, inputs=asdict(inputs),
                   heartbeat=dict(can_id=HEARTBEAT_ID, payload_hex=packet.hex(),
                                  delivered=not dropped), events=events)
        for key, held, released in [('watchdog','watchdog-held','watchdog-released'),
                                     ('safestop','latch-held','latch-released')]:
            if previous is None or previous[key] != row[key]:
                events.append(held if row[key] else released)
        if row['speed_mps'] == 0 and (previous is None or previous['speed_mps'] > 0):
            events.append('vehicle-stopped')
        yield row
        previous = row
