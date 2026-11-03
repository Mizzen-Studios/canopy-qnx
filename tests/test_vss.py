import json
from dataclasses import replace
from decimal import Decimal, localcontext
from pathlib import Path
import re
import unittest

from canopy_host.vss import (DISTANCE, SIGNALS, SPEED, STEERING, HostAdapter,
                             Update, decode, encode, qpp_text_write)

ROOT = Path(__file__).resolve().parents[1]


class CodecTests(unittest.TestCase):
    def test_hand_calculated_golden_vectors(self):
        fixture = json.loads((ROOT / 'vss/golden.json').read_text())
        self.assertIn('host simulation', fixture['source'])
        for vector in fixture['vectors']:
            with self.subTest(vector=vector):
                frame = vector['can_id'], bytes.fromhex(vector['hex'])
                self.assertEqual(decode(*frame),
                                 (vector['path'], Decimal(vector['value'])))
                self.assertEqual(encode(vector['path'], Decimal(vector['value'])), frame)

    def test_exhaustive_raw_domain(self):
        # Every possible 16-bit value for all three signals: valid roundtrip
        # or explicit rejection. Also exercises sign-extension and both endian.
        for signal in SIGNALS:
            for unsigned in range(65536):
                payload = unsigned.to_bytes(2, signal.byteorder)
                raw = unsigned - 65536 if signal.signed and unsigned >= 32768 else unsigned
                value = Decimal(raw) * signal.scale
                if signal.minimum <= value <= signal.maximum:
                    self.assertEqual(decode(signal.can_id, payload), (signal.path, value))
                    self.assertEqual(encode(signal.path, value), (signal.can_id, payload))
                else:
                    with self.assertRaises(ValueError):
                        decode(signal.can_id, payload)

    def test_unknown_ids_flags_and_types(self):
        for ident in (True, 256.0, '256', None, -1, 0x200, 0x80000100,
                      0x40000100, 0x20000100, 0x1100):
            with self.subTest(ident=ident), self.assertRaises(ValueError):
                decode(ident, b'00')

    def test_wrong_payload_type_or_length(self):
        for payload in (None, '00', [0, 0], bytearray(2), memoryview(b'00'),
                        b'', b'0', b'000', bytes(8), bytes(64)):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                decode(0x100, payload)

    def test_encode_rejects_invalid_or_lossy_values(self):
        for path, value in ((SPEED, -1), (SPEED, 250.01), (SPEED, .001),
                            (STEERING, -721), (STEERING, 721), (STEERING, .1),
                            (DISTANCE, 500.01), (DISTANCE, -.01),
                            (DISTANCE, .001), ('../Speed', 1), (None, 1)):
            with self.subTest(path=path, value=value), self.assertRaises(ValueError):
                encode(path, value)
        for value in (True, '12', None, float('nan'), float('inf'),
                      Decimal('sNaN'), Decimal('-Infinity')):
            with self.assertRaises(ValueError):
                encode(SPEED, value)

    def test_scaling_and_decimal_context(self):
        self.assertEqual(encode(SPEED, 12.34), (0x100, bytes.fromhex('d204')))
        self.assertEqual(encode(DISTANCE, 12.34), (0x102, bytes.fromhex('04d2')))
        self.assertEqual(decode(0x101, bytes.fromhex('ffff')), (STEERING, Decimal(-1)))
        with localcontext() as ctx:
            ctx.prec = 2
            self.assertEqual(decode(0x100, bytes.fromhex('d204'))[1], Decimal('12.34'))
            self.assertEqual(encode(SPEED, Decimal('12.34'))[1], bytes.fromhex('d204'))
            with self.assertRaises(ValueError):
                encode(SPEED, Decimal('12.341'))

    def test_dbc_matches_fixed_mapping(self):
        text = (ROOT / 'dbc/canopy-demo.dbc').read_text()
        messages = re.findall(r'BO_ (\d+) \w+: (\d+) HostSim\n SG_ \w+ : (\d+)\|16@([01])([+-]) \(([^,]+),0\) \[([^|]+)\|([^]]+)\] "([^"]+)" Canvss', text)
        self.assertEqual(len(messages), 3)
        for signal, (ident, dlc, start, endian, sign, scale, lo, hi, unit) in zip(SIGNALS, messages):
            self.assertEqual((int(ident), int(dlc), int(start), endian, sign),
                             (signal.can_id, 2, 0 if signal.byteorder == 'little' else 7,
                              '1' if signal.byteorder == 'little' else '0',
                              '-' if signal.signed else '+'))
            self.assertEqual((Decimal(scale), Decimal(lo), Decimal(hi), unit),
                             (signal.scale, signal.minimum, signal.maximum, signal.unit))

    def test_overlay_extension_is_explicit(self):
        text = (ROOT / 'vss/canopy-overlay.vspec').read_text()
        self.assertIn(DISTANCE + ':', text)
        self.assertIn('  datatype: float', text)
        self.assertIn('  unit: m', text)
        self.assertIn('  max: 500', text)


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.updates = []
        self.adapter = HostAdapter(self.updates.append)

    def receive(self, **kwargs):
        return self.adapter.receive(0x100, bytes.fromhex('d204'),
                                    **({'source': 'host simulation fixture',
                                        'received_ns': 123} | kwargs))

    def test_source_timestamp_and_units_preserved(self):
        update = self.receive()
        self.assertEqual(update, Update(SPEED, Decimal('12.34'), 'km/h',
                                        'host simulation fixture', 123))
        self.assertEqual(self.updates, [update])

    def test_no_sink_call_on_invalid_input(self):
        for kwargs in ({'source': ''}, {'source': '  '}, {'source': 'x\nQNX'},
                       {'source': None}, {'source': 'x' * 161},
                       {'received_ns': -1}, {'received_ns': True},
                       {'received_ns': 1.0}, {'is_fd': True}, {'is_fd': 0}):
            with self.assertRaises(ValueError):
                self.receive(**kwargs)
        with self.assertRaises(ValueError):
            self.adapter.receive(0x100, b'bad', source='host sim', received_ns=1)
        self.assertEqual(self.updates, [])

    def test_sink_failure_propagates(self):
        def fail(update):
            raise OSError('service disconnected')
        with self.assertRaises(OSError):
            HostAdapter(fail).receive(0x100, b'00', source='host sim', received_ns=1)
        with self.assertRaises(ValueError):
            HostAdapter(None)

    def test_text_intents_are_allowlisted_and_terminated(self):
        fixture = json.loads((ROOT / 'vss/golden.json').read_text())
        for v in fixture['vectors']:
            update = self.adapter.receive(v['can_id'], bytes.fromhex(v['hex']),
                                          source=fixture['source'], received_ns=1)
            intent = qpp_text_write(update)
            self.assertEqual(intent.filename, '/dev/signal/' + v['path'].replace('.', '/') + '?text')
            self.assertEqual(intent.payload, v['value'].encode() + b'\0')
            self.assertEqual(intent.update.source, fixture['source'])

    def test_text_intents_reject_path_and_metadata_injection(self):
        update = self.receive()
        for mount in ('relative', '/', '/dev//signal', '/dev/../signal',
                      '/dev/signal?text', '/dev/signal/', '/dev/\x00signal'):
            with self.assertRaises(ValueError):
                qpp_text_write(update, mount)
        for bad in (replace(update, path='../Speed'), replace(update, unit='m/s'),
                    replace(update, value=Decimal('1.001')), replace(update, source=''),
                    replace(update, received_ns=-1), None):
            with self.assertRaises(ValueError):
                qpp_text_write(bad)
        self.assertTrue(qpp_text_write(update, '/custom/signals').filename.startswith('/custom/signals/'))
