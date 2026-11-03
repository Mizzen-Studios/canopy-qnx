import unittest
from canopy_host.sim import simulate
from canopy_host.socketcan import pack, unpack


class SimulationTests(unittest.TestCase):
    def test_determinism(self):
        self.assertEqual(simulate(seed=7), simulate(seed=7))

    def test_all_faults_stop_vehicle(self):
        for scenario in ('drop', 'bad-crc', 'frozen', 'obstacle', 'stale', 'pilot'):
            records = simulate(scenario)
            self.assertTrue(all(r['source'].startswith('host deterministic') for r in records))
            at = {r['time_ms']: r for r in records}
            self.assertTrue(at[490]['accepted'], scenario)
            self.assertFalse(at[490]['watchdog'], scenario)
            self.assertEqual(at[3400]['speed_mps'], 0, scenario)
            self.assertEqual(at[3400]['brake'], 100, scenario)
            self.assertTrue(at[3400]['hazards'], scenario)
            if scenario in ('drop', 'bad-crc', 'frozen'):
                self.assertFalse(at[580]['watchdog'])
                self.assertTrue(at[590]['watchdog'])
            else:
                self.assertTrue(at[500]['safestop'])

    def test_socketcan_codec(self):
        self.assertEqual(unpack(pack(0x200, b'1234')), (0x200, b'1234'))
        for ident, payload in [(0x800, b''), (0x200, b'123456789')]:
            with self.assertRaises(ValueError):
                pack(ident, payload)
        for raw in [b'', b'0' * 16, pack(0x200, b'1234')[:4] + b'\x09' + b'\0' * 11]:
            with self.assertRaises(ValueError):
                unpack(raw)
