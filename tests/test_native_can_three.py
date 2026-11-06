import importlib.util
from pathlib import Path
import unittest

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

if __name__ == '__main__':
    unittest.main()
