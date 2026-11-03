import unittest
from canopy_host.protocol import Heartbeat, State, crc8
from canopy_host.safety import Actuator, Inputs, Safestop


class ProtocolTests(unittest.TestCase):
    def test_crc_known_answer(self):
        self.assertEqual(crc8(b'123456789'), 0x4b)

    def test_roundtrip_all_counters_and_states(self):
        for state in State:
            for counter in range(16):
                h = Heartbeat(state, 100 if state == State.SAFE_STOP else 25, counter)
                self.assertEqual(Heartbeat.decode(0x200, h.encode()), h)

    def test_every_single_bit_corruption(self):
        payload = Heartbeat(State.DRIVE, 0, 7).encode()
        for bit in range(32):
            bad = bytearray(payload)
            bad[bit // 8] ^= 1 << (bit % 8)
            with self.assertRaises(ValueError):
                Heartbeat.decode(0x200, bytes(bad))

    def test_invalid_fields(self):
        for h in [Heartbeat(State.DRIVE, 101, 0), Heartbeat(State.DRIVE, 0, 16),
                  Heartbeat(State.SAFE_STOP, 0, 1)]:
            with self.assertRaises(ValueError):
                h.encode()
        for ident, payload in [(0x201, b'1234'), (0x200, b''), (0x200, b'12345')]:
            with self.assertRaises(ValueError):
                Heartbeat.decode(ident, payload)


class LatchTests(unittest.TestCase):
    def test_ten_fresh_and_ramp(self):
        stop = Safestop()
        for i in range(9):
            self.assertEqual(stop.cycle(i * 10, Inputs()).state, State.SAFE_STOP)
        self.assertEqual(stop.cycle(90, Inputs()).state, State.SAFE_STOP)
        self.assertFalse(stop.latched)
        self.assertEqual(stop.brake, 100)
        for i in range(10, 20):
            stop.cycle(i * 10, Inputs())
        self.assertEqual(stop.brake, 0)

    def test_each_fault_latches_and_pilot_cannot_clear(self):
        for fault in [Inputs(speed_age_ms=31), Inputs(obstacle_age_ms=31),
                      Inputs(obstacle_m=5), Inputs(pilot_speed_mps=21),
                      Inputs(pilot_speed_mps=float('nan')), Inputs(obstacle_m=float('inf'))]:
            stop = Safestop()
            for i in range(20):
                stop.cycle(i * 10, Inputs())
            self.assertEqual(stop.cycle(200, fault).state, State.SAFE_STOP)
            for i in range(9):
                self.assertEqual(stop.cycle(210 + i * 10, Inputs(pilot_speed_mps=20)).state,
                                 State.SAFE_STOP)
            self.assertTrue(stop.latched)

    def test_unhealthy_cycle_resets_streak(self):
        stop = Safestop()
        for i in range(8):
            stop.cycle(i * 10, Inputs())
        stop.cycle(80, Inputs(obstacle_m=0))
        for i in range(9):
            stop.cycle(90 + i * 10, Inputs())
        self.assertTrue(stop.latched)

    def test_gap_and_duplicate_clock(self):
        stop = Safestop()
        for i in range(20):
            stop.cycle(i * 10, Inputs())
        self.assertEqual(stop.cycle(220, Inputs()).state, State.SAFE_STOP)
        with self.assertRaises(ValueError):
            stop.cycle(220, Inputs())


def armed():
    ecu = Actuator()
    for i in range(10):
        ecu.receive(i * 10, 0x200, Heartbeat(State.SAFE_STOP, 100, i).encode())
    assert ecu.receive(100, 0x200, Heartbeat(State.DRIVE, 0, 10).encode())
    return ecu


class ActuatorTests(unittest.TestCase):
    def test_timeout_exact_boundary(self):
        ecu = armed()
        ecu.advance(199)
        self.assertFalse(ecu.timeout)
        ecu.advance(200)
        self.assertTrue(ecu.timeout)
        self.assertEqual((ecu.brake, ecu.hazards), (100, True))
        ecu.advance(3000)
        self.assertEqual(ecu.speed_mps, 0)

    def test_frozen_bad_crc_and_out_of_order_never_refresh(self):
        for kind in ['frozen', 'crc', 'backward', 'skip', 'id']:
            ecu = armed()
            for now in range(110, 201, 10):
                counter = {'frozen': 10, 'backward': 9, 'skip': 12}.get(kind, 11)
                payload = Heartbeat(State.DRIVE, 0, counter).encode()
                if kind == 'crc':
                    payload = payload[:-1] + bytes([payload[-1] ^ 1])
                self.assertFalse(ecu.receive(now, 0x201 if kind == 'id' else 0x200, payload))
            self.assertEqual(ecu.last_valid_ms, 100)
            self.assertTrue(ecu.timeout)

    def test_wrap(self):
        ecu = armed()
        for i in range(11, 34):
            self.assertTrue(ecu.receive(i * 10, 0x200,
                                       Heartbeat(State.DRIVE, 0, i % 16).encode()))

    def test_delayed_receive_cannot_hide_timeout(self):
        ecu = armed()
        self.assertFalse(ecu.receive(201, 0x200, Heartbeat(State.DRIVE, 0, 11).encode()))
        self.assertTrue(ecu.timeout)

    def test_recovery_requires_ten_safe_fresh_frames(self):
        ecu = armed()
        ecu.advance(200)
        for i in range(9):
            self.assertFalse(ecu.receive(210 + 10 * i, 0x200,
                                        Heartbeat(State.SAFE_STOP, 100, (i + 11) % 16).encode()))
            self.assertTrue(ecu.timeout)
        self.assertTrue(ecu.receive(300, 0x200, Heartbeat(State.SAFE_STOP, 100, 4).encode()))
        self.assertFalse(ecu.timeout)
        self.assertEqual(ecu.brake, 100)

    def test_frozen_recovery_cannot_release(self):
        ecu = Actuator()
        for i in range(30):
            ecu.receive(i * 10, 0x200, Heartbeat(State.SAFE_STOP, 100, 7).encode())
        self.assertTrue(ecu.timeout)

    def test_clock_backwards(self):
        ecu = armed()
        with self.assertRaises(ValueError):
            ecu.advance(90)


if __name__ == '__main__':
    unittest.main()
