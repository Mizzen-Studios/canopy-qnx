"""Strict host-run JSONL reader/writer; sources are provenance, not authentication."""
import json
import math
from pathlib import Path
from .director import EVENTS, SCHEMA, SOURCE
from .protocol import Heartbeat

MAX_BYTES = 2_000_000
MAX_ROWS = 10000
SAFE = 9007199254740991


def integer(value, minimum=0):
    return type(value) is int and minimum <= value <= SAFE


def validate(rows):
    if not rows or len(rows) > MAX_ROWS:
        raise ValueError('Use 1–10000 host simulation records')
    last = -1
    identity = None
    for index, r in enumerate(rows):
        try:
            valid = (r['schema'] == SCHEMA and r['source'] == SOURCE and
                     r['scenario'] == 'hero' and r['clock'] == 'logical-ms' and
                     integer(r['seed'], -SAFE) and integer(r['sequence']) and
                     r['sequence'] == index and integer(r['time_ms']) and
                     r['time_ms'] > last and
                     all(type(r[k]) is bool for k in ('hazards','watchdog','safestop','accepted')) and
                     all(type(r[k]) in (int,float) and math.isfinite(r[k]) and r[k] >= 0
                         for k in ('speed_mps','brake')) and r['brake'] <= 100 and
                     type(r['events']) is list and len(set(r['events'])) == len(r['events']) and
                     all(e in EVENTS for e in r['events']))
            inputs = r['inputs']
            valid &= (set(inputs) == {'speed_age_ms','obstacle_age_ms','obstacle_m','pilot_speed_mps'} and
                      all(type(v) in (int,float) and math.isfinite(v) and v >= 0 for v in inputs.values()))
            h = r['heartbeat']
            valid &= (h['can_id'] == 512 and type(h['can_id']) is int and
                      type(h['delivered']) is bool and type(h['payload_hex']) is str and
                      len(h['payload_hex']) == 8)
            Heartbeat.decode(h['can_id'], bytes.fromhex(h['payload_hex']))
            current = (r['source'], r['schema'], r['scenario'], r['seed'])
            valid &= identity is None or identity == current
            if not valid:
                raise ValueError('unsupported values')
            identity, last = current, r['time_ms']
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as error:
            raise ValueError(f'Invalid host record at line {index + 1}: {error}') from error
    return rows


def decode(text):
    if len(text.encode('utf-8')) > MAX_BYTES:
        raise ValueError('File exceeds 2 MB limit')
    try:
        rows = [json.loads(line) for line in text.strip().splitlines()]
    except (ValueError, TypeError) as error:
        raise ValueError('Invalid JSONL') from error
    return validate(rows)


def read_run(path):
    with open(path, 'rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('File exceeds 2 MB limit')
    return decode(data.decode('utf-8'))


def encode(rows):
    return ''.join(json.dumps(r, sort_keys=True, allow_nan=False) + '\n' for r in validate(list(rows)))


def write_run(path, rows):
    # Exclusive creation: a recording never silently replaces existing evidence.
    text = encode(rows)
    if len(text.encode('utf-8')) > MAX_BYTES:
        raise ValueError('File exceeds 2 MB limit')
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(text)
