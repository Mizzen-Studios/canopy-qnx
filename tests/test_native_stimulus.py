import unittest
from unittest.mock import patch
from tools.native_safestop_host import stimulus

class NativeStimulusTests(unittest.TestCase):
    def test_faults_use_existing_ids_and_close(self):
        for scenario in ('healthy','stale','obstacle','pilot','malformed'):
            with self.subTest(scenario=scenario), patch('tools.native_safestop_host.SocketCAN') as bus,                     patch('tools.native_safestop_host.time.monotonic',side_effect=[0,0,2.5,4.5,8]),                     patch('tools.native_safestop_host.time.sleep'):
                stimulus('test-only',8,scenario)
                frames = [c.args for c in bus.return_value.send.call_args_list]
                self.assertTrue(all(f[0] in (0x100,0x102) for f in frames))
                self.assertEqual(len(frames),4 if scenario=='stale' else 6)
                if scenario=='obstacle': self.assertEqual(frames[3],(0x102,b'\x00\x64'))
                if scenario=='pilot': self.assertEqual(frames[2],(0x100,b'\x28\x23'))
                if scenario=='malformed': self.assertEqual(frames[3],(0x102,b'\x00'))
                self.assertEqual(frames[-2:],[(0x100,b'\x10\x0e'),(0x102,b'\x27\x10')])
                bus.return_value.close.assert_called_once()

    def test_invalid_never_opens_bus(self):
        with patch('tools.native_safestop_host.SocketCAN') as bus:
            for args in [('x',8,'unknown'),('x',float('nan'),'healthy'),('x',61,'healthy')]:
                with self.assertRaises(ValueError): stimulus(*args)
            bus.assert_not_called()

    def test_send_failure_closes_without_success(self):
        with patch('tools.native_safestop_host.SocketCAN') as bus,                 patch('tools.native_safestop_host.time.monotonic',side_effect=[0,0]):
            bus.return_value.send.side_effect = OSError('transport failed')
            with self.assertRaises(OSError): stimulus('x',8,'healthy')
            bus.return_value.close.assert_called_once()
