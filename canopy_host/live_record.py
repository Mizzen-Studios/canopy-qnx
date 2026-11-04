"""HOST VCAN recording contract and raw runtime adapter; no provenance relabeling."""
import json
import math
from pathlib import Path
from .runtime import SOURCE
from .protocol import Heartbeat
from .record import integer

SCHEMA = 'canopy.host-vcan-run.v1'


def validate(rows):
    last = -1
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            raise ValueError('HOST VCAN record must be an object')
        try:
            ok = (r['schema'] == SCHEMA and r['source'] == SOURCE and
                  r['clock'] == 'host-monotonic-ns' and r['scenario'] == 'host-session' and
                  integer(r['sequence']) and r['sequence'] == i and integer(r['monotonic_ns']) and
                  r['monotonic_ns'] > last and integer(r['origin_ns']) and
                  r['time_ms'] == (r['monotonic_ns'] - r['origin_ns']) / 1e6 and
                  r['time_ms'] >= 0 and r['origin_ns'] == rows[0]['origin_ns'] and
                  type(r['interface']) is str and r['interface'] == rows[0]['interface'] and
                  bool(r['interface']) and len(r['interface']) <= 15 and
                  all(integer(r[k], 1) for k in ('actuator_pid', 'sender_pid')) and
                  all(type(r[k]) is bool for k in ('hazards', 'watchdog', 'safestop', 'accepted')) and
                  all(type(r[k]) in (int, float) and math.isfinite(r[k]) and r[k] >= 0
                      for k in ('speed_mps', 'brake')) and r['brake'] <= 100 and r['events'] == [])
            inp = r['inputs']
            ok &= (set(inp) == {'speed_age_ms', 'obstacle_age_ms', 'obstacle_m', 'pilot_speed_mps'} and
                   all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in inp.values()))
            h = r['heartbeat']
            ok &= type(h['can_id']) is int and h['can_id'] == 512 and type(h['delivered']) is bool and type(h['payload_hex']) is str and len(h['payload_hex']) == 8
            Heartbeat.decode(h['can_id'], bytes.fromhex(h['payload_hex']))
            if not ok:
                raise ValueError('unsupported values')
            last = r['monotonic_ns']
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError, IndexError) as e:
            raise ValueError(f'Invalid HOST VCAN record at line {i+1}: {e}') from e
    if not rows or len(rows) > 10000:
        raise ValueError('Use 1–10000 HOST VCAN records')
    return rows


def convert(directory):
    """Join measured agent snapshots to preceding sender/ECU observations.

    No interpolated state, invented heartbeat receipt, or logical clock. Raw
    role logs remain the evidence; this is a 20 Hz offline viewing projection.
    Rotated logs are loaded oldest first; missing observations fail closed.
    """
    directory = Path(directory)
    def read(name):
        paths = [directory / (name + f'.jsonl.{i}') for i in (3, 2, 1)] + [directory / (name + '.jsonl')]
        rows = [json.loads(line) for p in paths if p.exists() for line in p.read_text().splitlines()]
        if not rows or any(not isinstance(r, dict) or r.get('schema') != 'canopy.host-runtime.v1' or r.get('source') != SOURCE or
                           not integer(r.get('monotonic_ns')) or not integer(r.get('pid'), 1) for r in rows):
            raise ValueError('invalid raw host runtime provenance')
        if any(b['monotonic_ns'] <= a['monotonic_ns'] for a, b in zip(rows, rows[1:])):
            raise ValueError('raw runtime time must increase')
        return rows
    agents = [r for r in read('session') if r['event'] == 'host-agent']
    senders = [r for r in read('sender') if r['event'] == 'heartbeat']
    ecus = [r for r in read('actuator') if r['event'] == 'actuator']
    if not senders or not ecus:
        raise ValueError('missing sender/actuator observations')
    lower = max(senders[0]['monotonic_ns'], ecus[0]['monotonic_ns'])
    upper = min(senders[-1]['monotonic_ns'], ecus[-1]['monotonic_ns'])
    agents = [a for a in agents if lower <= a['monotonic_ns'] <= upper]
    result = []
    si = ei = 0
    for a in agents:
        stamp = a['monotonic_ns']
        while si+1 < len(senders) and senders[si+1]['monotonic_ns'] <= stamp:
            si += 1
        while ei+1 < len(ecus) and ecus[ei+1]['monotonic_ns'] <= stamp:
            ei += 1
        if not senders or not ecus:
            raise ValueError('missing sender/actuator observations')
        s, e = senders[si], ecus[ei]
        if max(s['monotonic_ns'], e['monotonic_ns']) > stamp:
            continue  # Startup before either role had any observation.
        if stamp - min(s['monotonic_ns'], e['monotonic_ns']) > 100_000_000:
            raise ValueError('runtime observation gap exceeds 100 ms')
        if s['pid'] != a['sender_pid'] or e['pid'] != a['actuator_pid']:
            raise ValueError('role PID mismatch')
        age = (stamp - a['inputs']['monotonic_ns']) / 1e6
        if age < 0:
            raise ValueError('future sensor timestamp')
        origin = result[0]['origin_ns'] if result else stamp
        result.append(dict(schema=SCHEMA, source=SOURCE, clock='host-monotonic-ns',
                           scenario='host-session', sequence=len(result), monotonic_ns=stamp,
                           origin_ns=origin, time_ms=(stamp-origin)/1e6, interface=a['interface'],
                           actuator_pid=e['pid'], sender_pid=s['pid'], speed_mps=e['speed_mps'],
                           brake=e['brake'], hazards=e['hazards'], watchdog=e['watchdog'],
                           safestop=s['latched'], accepted=e['accepted'] is True, events=[],
                           heartbeat=dict(can_id=512, payload_hex=s['payload_hex'],
                                          delivered=e['accepted'] is True and e['received_hex'] == s['payload_hex']),
                           inputs=dict(speed_age_ms=age, obstacle_age_ms=age,
                                       obstacle_m=a['inputs']['obstacle_m'],
                                       pilot_speed_mps=a['inputs']['pilot_speed_mps'])))
    return validate(result)
