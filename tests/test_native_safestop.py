"""Host-compiled original C core: not native QNX runtime acceptance."""
import ctypes as C
import math
from pathlib import Path
import random
import subprocess
import tempfile
import unittest
from canopy_host.protocol import Heartbeat, State, crc8
from canopy_host.safety import Actuator, Inputs, Safestop

ROOT = Path(__file__).resolve().parents[1]

class CInputs(C.Structure):
    _fields_ = [('speed_age_ms', C.c_int64), ('obstacle_age_ms', C.c_int64),
                ('obstacle_m', C.c_double), ('pilot_speed_mps', C.c_double)]

class CStop(C.Structure):
    _fields_ = [('latched', C.c_bool), ('has_time', C.c_bool),
                ('fresh_cycles', C.c_uint), ('brake', C.c_uint),
                ('counter', C.c_uint), ('last_ms', C.c_uint64)]

class Packet(C.Structure):
    _fields_ = [('state', C.c_uint), ('brake', C.c_uint), ('counter', C.c_uint)]

class NativeSafestopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / 'build').mkdir(exist_ok=True)
        cls.tmp = tempfile.TemporaryDirectory(dir=ROOT / 'build')
        cls.addClassCleanup(cls.tmp.cleanup)
        library = Path(cls.tmp.name) / 'safestop.so'
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic',
                        '-O2', '-shared', '-fPIC', str(ROOT / 'safety/safestop.c'),
                        '-o', str(library)], check=True, capture_output=True)
        cls.lib = C.CDLL(str(library))
        cls.lib.canopy_safestop_init.argtypes = [C.POINTER(CStop)]
        cls.lib.canopy_safestop_cycle.argtypes = [C.POINTER(CStop), C.c_uint64,
                                                C.POINTER(CInputs), C.POINTER(Packet)]
        cls.lib.canopy_safestop_cycle.restype = C.c_bool
        cls.lib.canopy_heartbeat_encode.argtypes = [C.POINTER(Packet), C.POINTER(C.c_uint8)]
        cls.lib.canopy_heartbeat_encode.restype = C.c_bool
        cls.lib.canopy_heartbeat_decode.argtypes = [C.c_uint32, C.POINTER(C.c_uint8),
                                                  C.c_size_t, C.POINTER(Packet)]
        cls.lib.canopy_heartbeat_decode.restype = C.c_bool
        cls.lib.canopy_crc8.argtypes = [C.POINTER(C.c_uint8), C.c_size_t]
        cls.lib.canopy_crc8.restype = C.c_uint8

    def new_stop(self):
        s = CStop()
        self.lib.canopy_safestop_init(C.byref(s))
        return s

    def cycle(self, s, now, inputs=Inputs()):
        i = CInputs(inputs.speed_age_ms, inputs.obstacle_age_ms,
                    inputs.obstacle_m, inputs.pilot_speed_mps)
        p = Packet()
        self.assertTrue(self.lib.canopy_safestop_cycle(C.byref(s), now, C.byref(i), C.byref(p)))
        return p

    def encode(self, p):
        out = (C.c_uint8 * 4)()
        self.assertTrue(self.lib.canopy_heartbeat_encode(C.byref(p), out))
        return bytes(out)

    def decode(self, raw, ident=0x200):
        data = (C.c_uint8 * len(raw))(*raw)
        out = Packet(99, 99, 99)
        ok = self.lib.canopy_heartbeat_decode(ident, data, len(raw), C.byref(out))
        if not ok:
            self.assertEqual((out.state, out.brake, out.counter), (99, 99, 99))
        return ok

    def test_protocol_parity_and_corruption(self):
        known = b'123456789'
        self.assertEqual(self.lib.canopy_crc8((C.c_uint8 * len(known))(*known), len(known)), 0x4b)
        for state in State:
            for counter in range(16):
                brake = 100 if state == State.SAFE_STOP else 25
                raw = self.encode(Packet(state, brake, counter))
                self.assertEqual(raw, Heartbeat(state, brake, counter).encode())
                self.assertTrue(self.decode(raw))
                for bit in range(32):
                    bad = bytearray(raw)
                    bad[bit // 8] ^= 1 << (bit % 8)
                    self.assertFalse(self.decode(bad))
        for body in [bytes([4, 0, 0]), bytes([0, 101, 0]),
                     bytes([0, 0, 16]), bytes([2, 0, 0])]:
            self.assertFalse(self.decode(body + bytes([crc8(b'\x02\x00' + body)])))
        for raw, ident in [(b'', 0x200), (b'12345', 0x200), (b'1234', 0x201),
                           (Heartbeat(State.DRIVE, 0, 0).encode(), 0x80000200)]:
            self.assertFalse(self.decode(raw, ident))
        for p in [Packet(4, 0, 0), Packet(0, 101, 0), Packet(0, 0, 16), Packet(2, 0, 0)]:
            self.assertFalse(self.lib.canopy_heartbeat_encode(C.byref(p), (C.c_uint8 * 4)()))

    def test_hard_faults_ten_fresh_and_ramp_parity(self):
        faults = [Inputs(speed_age_ms=31), Inputs(obstacle_age_ms=31),
                  Inputs(speed_age_ms=-1), Inputs(obstacle_age_ms=-1),
                  Inputs(obstacle_m=5), Inputs(obstacle_m=-1),
                  Inputs(obstacle_m=math.nan), Inputs(obstacle_m=math.inf),
                  Inputs(pilot_speed_mps=21), Inputs(pilot_speed_mps=-1),
                  Inputs(pilot_speed_mps=math.nan), Inputs(pilot_speed_mps=math.inf)]
        for fault in faults:
            s, py = self.new_stop(), Safestop()
            sequence = [Inputs()] * 25 + [fault] + [Inputs()] * 9 + [fault] + [Inputs()] * 25
            for n, inputs in enumerate(sequence):
                packet = self.cycle(s, n * 10, inputs)
                expected = py.cycle(n * 10, inputs)
                self.assertEqual(self.encode(packet), expected.encode())
                self.assertEqual(s.latched, py.latched)
            self.assertFalse(s.latched)
            self.assertEqual(s.brake, 0)

    def test_time_gap_duplicate_backwards_and_large_clock(self):
        s = self.new_stop()
        for n in range(25):
            self.cycle(s, n * 10)
        self.assertEqual(self.cycle(s, 261).state, State.SAFE_STOP)
        before = bytes(s)
        for now in [261, 260, 0]:
            p, inputs = Packet(99, 99, 99), CInputs(0, 0, 100, 10)
            self.assertFalse(self.lib.canopy_safestop_cycle(C.byref(s), now, C.byref(inputs), C.byref(p)))
            self.assertEqual(bytes(s), before)
            self.assertEqual(p.state, 99)
        self.assertEqual(self.cycle(s, 2**64 - 1).state, State.SAFE_STOP)

    def test_seeded_mixed_sequence_and_long_running_saturation(self):
        rng, s, py, now = random.Random(7), self.new_stop(), Safestop(), 0
        for _ in range(4000):
            now += rng.choice([10, 10, 20, 21])
            inputs = Inputs(speed_age_ms=rng.choice([0, 30, 31]),
                            obstacle_m=rng.choice([5, 5.01, 100]),
                            pilot_speed_mps=rng.choice([0, 20, 21]))
            self.assertEqual(self.encode(self.cycle(s, now, inputs)), py.cycle(now, inputs).encode())
        for _ in range(10000):
            now += 10
            self.assertEqual(self.encode(self.cycle(s, now)), py.cycle(now, Inputs()).encode())
        self.assertEqual(s.fresh_cycles, 12)

    def test_c_encoded_heartbeat_existing_actuator_frozen_crc_timeout(self):
        for fault in ['frozen', 'crc', 'skip']:
            s, ecu = self.new_stop(), Actuator()
            for n in range(25):
                raw = self.encode(self.cycle(s, n * 10))
                ecu.receive(n * 10, 0x200, raw)
            self.assertFalse(ecu.timeout)
            self.assertEqual(ecu.brake, 0)
            last = ecu.last_valid_ms
            for n in range(25, 36):
                if fault == 'crc':
                    bad = self.encode(self.cycle(s, n * 10))
                    bad = bad[:-1] + bytes([bad[-1] ^ 1])
                elif fault == 'skip':
                    bad = self.encode(Packet(State.DRIVE, 0, (ecu.counter + 2) % 16))
                else:
                    bad = raw
                self.assertFalse(ecu.receive(n * 10, 0x200, bad))
            self.assertEqual(ecu.last_valid_ms, last)
            self.assertTrue(ecu.timeout)
            self.assertEqual((ecu.brake, ecu.hazards), (100, True))

if __name__ == '__main__':
    unittest.main()
