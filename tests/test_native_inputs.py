"""Host compilation only; no mocked native runtime acceptance."""
import ctypes as C
from pathlib import Path
import subprocess
import tempfile
import unittest
from canopy_host.protocol import State
from canopy_host.safety import Actuator
from test_native_safestop import CInputs, CStop, Packet
ROOT = Path(__file__).resolve().parents[1]

class Sensors(C.Structure):
    _fields_ = [('speed_seen', C.c_bool), ('obstacle_seen', C.c_bool),
                ('speed_ms', C.c_uint64), ('obstacle_ms', C.c_uint64),
                ('speed_mps', C.c_double), ('obstacle_m', C.c_double)]

class NativeInputsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT/'build').mkdir(exist_ok=True)
        cls.tmp = tempfile.TemporaryDirectory(dir=ROOT/'build')
        cls.addClassCleanup(cls.tmp.cleanup)
        so = Path(cls.tmp.name)/'inputs.so'
        subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-pedantic','-O2',
                        '-shared','-fPIC',str(ROOT/'safety/native_inputs.c'),
                        str(ROOT/'safety/safestop.c'),'-o',str(so)],check=True,capture_output=True)
        cls.lib = C.CDLL(str(so))
        cls.lib.canopy_sensor_receive.argtypes = [C.POINTER(Sensors), C.c_uint64,
                                                 C.c_uint32,C.POINTER(C.c_uint8),C.c_size_t]
        cls.lib.canopy_sensor_receive.restype = C.c_bool
        cls.lib.canopy_sensor_snapshot.argtypes = [C.POINTER(Sensors),C.c_uint64]
        cls.lib.canopy_sensor_snapshot.restype = CInputs
        cls.lib.canopy_safestop_init.argtypes = [C.POINTER(CStop)]
        cls.lib.canopy_safestop_cycle.argtypes = [C.POINTER(CStop),C.c_uint64,C.POINTER(CInputs),C.POINTER(Packet)]
        cls.lib.canopy_safestop_cycle.restype = C.c_bool
        cls.lib.canopy_heartbeat_encode.argtypes = [C.POINTER(Packet),C.POINTER(C.c_uint8)]
        cls.lib.canopy_heartbeat_encode.restype = C.c_bool

    def send(self, s, now, ident, raw):
        return self.lib.canopy_sensor_receive(C.byref(s),now,ident,
                    (C.c_uint8*len(raw))(*raw),len(raw))

    def test_mapping_missing_malformed_future_and_flags(self):
        s = Sensors()
        self.assertEqual(self.lib.canopy_sensor_snapshot(C.byref(s),0).speed_age_ms,-1)
        self.assertTrue(self.send(s,100,0x100,b'\x10\x0e')) # 36km/h
        self.assertTrue(self.send(s,100,0x102,b'\x27\x10')) # 100m
        i = self.lib.canopy_sensor_snapshot(C.byref(s),130)
        self.assertEqual((i.speed_age_ms,i.obstacle_age_ms,i.pilot_speed_mps,i.obstacle_m),(30,30,10,100))
        self.assertEqual(self.lib.canopy_sensor_snapshot(C.byref(s),99).speed_age_ms,-1)
        self.assertFalse(self.send(s,140,0x80000100,b'\x00\x00'))
        self.assertFalse(self.send(s,140,0x100,b'\x00'))
        self.assertFalse(self.send(s,140,0x102,b'\xff\xff'))
        i = self.lib.canopy_sensor_snapshot(C.byref(s),140)
        self.assertEqual((i.speed_age_ms,i.obstacle_age_ms),(-1,-1))

    def test_existing_wire_core_and_independent_ecu_faults(self):
        for fault in ('stale','obstacle','pilot','malformed','kill','crc','frozen'):
            with self.subTest(fault=fault):
                sensors, stop, ecu = Sensors(), CStop(), Actuator()
                self.lib.canopy_safestop_init(C.byref(stop))
                frozen = None
                for n in range(100):
                    now = n*10
                    active = 30 <= n < 60
                    if not (active and fault == 'stale'):
                        self.send(sensors,now,0x100,b'\x28\x23' if active and fault=='pilot' else b'\x10\x0e')
                        self.send(sensors,now,0x102,b'\x00' if active and fault=='malformed' else
                                  b'\x00\x64' if active and fault=='obstacle' else b'\x27\x10')
                    i = self.lib.canopy_sensor_snapshot(C.byref(sensors),now)
                    packet = Packet()
                    self.assertTrue(self.lib.canopy_safestop_cycle(C.byref(stop),now,C.byref(i),C.byref(packet)))
                    data = (C.c_uint8*4)()
                    self.assertTrue(self.lib.canopy_heartbeat_encode(C.byref(packet),data))
                    raw = bytes(data)
                    if n == 29: frozen = raw
                    if active and fault=='crc': raw = raw[:-1]+bytes([raw[-1]^1])
                    if active and fault=='frozen': raw = frozen
                    if not (active and fault=='kill'): ecu.receive(now,0x200,raw)
                    else: ecu.advance(now)
                    if n==29: self.assertEqual((ecu.brake,ecu.timeout),(0,False))
                    if n==59:
                        self.assertEqual((ecu.brake,ecu.hazards),(100,True))
                        if fault in ('kill','crc','frozen'): self.assertTrue(ecu.timeout)
                        else: self.assertTrue(stop.latched)
                    if n==68 and fault in ('stale','obstacle','pilot','malformed'):
                        self.assertEqual(packet.state,State.SAFE_STOP)
                    if n==69 and fault in ('stale','obstacle','pilot','malformed'):
                        self.assertEqual((packet.state,packet.brake),(State.SAFE_STOP,100))
                if fault in ('kill','crc','frozen'):
                    # Sender never reset/rearmed: DRIVE cannot clear ECU watchdog.
                    self.assertTrue(ecu.timeout)
                else:
                    self.assertEqual((ecu.brake,ecu.timeout),(0,False))
                ecu.advance(4000)
                self.assertEqual((ecu.brake,ecu.hazards,ecu.speed_mps),(100,True,0))

    def test_adapter_is_not_host_buildable(self):
        r = subprocess.run(['cc','-fsyntax-only','-I'+str(ROOT/'safety'),
                            str(ROOT/'native/safestop_qnx.c')],capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('requires the QNX target',r.stderr)

if __name__ == '__main__': unittest.main()
