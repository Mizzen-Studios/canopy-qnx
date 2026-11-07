import importlib.util
from pathlib import Path
import unittest
import json
import tempfile
import sys

spec = importlib.util.spec_from_file_location('native_three', Path(__file__).parents[1]/'tools/native_can_three.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class NativeGateTests(unittest.TestCase):
    def setUp(self):
        self.frames = [(i, i.to_bytes(8, 'little').hex()) for i in range(100)]

    def test_exact_ordered(self):
        gate.require_exact(self.frames, list(self.frames))

    def test_reject_count_order_payload_and_constant(self):
        for rows in ([], self.frames[:-1], self.frames + self.frames[:1],
                     self.frames[::-1], [(0, 'ff'*8)]+self.frames[1:],
                     [(0, '00'*8)]*100,
                     [(0x800+i, data) for i, data in self.frames],
                     [(i, data[:-2]) for i, data in self.frames]):
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                gate.require_exact(self.frames, rows)

    def test_native_parser_and_reject_malformed(self):
        rows = gate.parse_qnx('  /dev/can0/rx0 TS: 123ms [SFF] 00A [8] 00 01 02 03 04 05 06 FF\r\n')
        self.assertEqual(rows, [(10, '00010203040506ff')])
        for text in ('/dev/can0/rx0 corrupt', '/dev/can0/rx0 TS: 1ms [SFF] A [7] 00'):
            with self.assertRaises(ValueError):
                gate.parse_qnx(text)

    def test_native_caps_are_distinct(self):
        script=(Path(__file__).parents[1]/'scripts/qemu-native-capped.sh').read_text()
        self.assertIn('CPUQuota=100%', script)
        self.assertIn('MemoryMax=1G', script)
        self.assertIn('nice -n 15', script)

class OfflineEvidenceTests(unittest.TestCase):
    def test_failed_summary_rejected(self):
        sys.path.insert(0, str(Path(__file__).parents[1]/'tools'))
        from verify_native_can_evidence import verify
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p/'summary.json').write_text(json.dumps({'pass':False, 'runs':[]}))
            with self.assertRaises(ValueError):
                verify(p)

    def test_wrong_source_rejected(self):
        sys.path.insert(0, str(Path(__file__).parents[1]/'tools'))
        from verify_native_can_evidence import verify
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p/'summary.json').write_text(json.dumps({'pass':True, 'runs':[1,2,3], 'sourceGate':'SocketCAN'}))
            with self.assertRaises(ValueError):
                verify(p)

if __name__ == '__main__':
    unittest.main()
