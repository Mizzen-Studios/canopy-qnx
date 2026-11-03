import io
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from canopy_host.runtime import load_inputs, emit
from canopy_host.runtime_runner import run_scenario
from canopy_host.safety import Safestop, Inputs
from canopy_host.protocol import State


class RuntimeTests(unittest.TestCase):
    def test_source_tagged_monotonic_record(self):
        out = io.StringIO()
        emit(out, 'test', value=4)
        record = json.loads(out.getvalue())
        self.assertIn('NOT QNX', record['source'])
        self.assertGreater(record['monotonic_ns'], 0)
        self.assertEqual(record['pid'], os.getpid())

    def test_snapshot_age_and_pilot_cannot_clear(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'in.json'
            path.write_text(json.dumps(dict(monotonic_ns=1000000, obstacle_m=100,
                                            pilot_speed_mps=10, clear_latch=True)))
            self.assertEqual(load_inputs(path, 32000000).speed_age_ms, 31)
            stop = Safestop()
            for i in range(9):
                self.assertEqual(stop.cycle(i*10, load_inputs(path, 1000000)).state,
                                 State.SAFE_STOP)
                self.assertTrue(stop.latched)
            self.assertEqual(stop.cycle(90, Inputs()).state, State.SAFE_STOP)
            self.assertFalse(stop.latched)
            self.assertEqual(stop.cycle(100, Inputs()).brake, 90)

    def test_missing_malformed_future_nonfinite_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'in.json'
            self.assertGreater(load_inputs(path, 100).speed_age_ms, 30)
            for data in ['{', '{}', '[]', 'null',
                         '{"monotonic_ns":101,"obstacle_m":100,"pilot_speed_mps":10}',
                         '{"monotonic_ns":true,"obstacle_m":100,"pilot_speed_mps":10}',
                         '{"monotonic_ns":0,"obstacle_m":NaN,"pilot_speed_mps":10}']:
                path.write_text(data)
                self.assertGreater(load_inputs(path, 100).speed_age_ms, 30)

    def test_unknown_scenario_rejected_before_spawn(self):
        with self.assertRaises(ValueError):
            run_scenario('unused', 'not-a-scenario')


@unittest.skipUnless(os.environ.get('CANOPY_LIVE_VCAN') == '1',
                     'opt-in Linux vcan test; set CANOPY_LIVE_VCAN=1 with vcan0 UP')
class LiveRuntimeTests(unittest.TestCase):
    def test_live_seven_faults_and_cleanup(self):
        with tempfile.TemporaryDirectory() as root:
            for name in ['stale', 'obstacle', 'pilot', 'sigstop', 'kill', 'bad-crc', 'frozen']:
                with self.subTest(scenario=name):
                    result = run_scenario(Path(root) / name, name,
                                          os.environ.get('CANOPY_CAN_INTERFACE', 'vcan0'))
                    self.assertTrue(result['passed'])
                    for pid in [result['sender_pid'], result['actuator_pid']]:
                        with self.assertRaises(ProcessLookupError):
                            os.kill(pid, 0)
