"""Host source-contract checks, never QNX execution evidence."""
from pathlib import Path
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]
class GuestQueryContract(unittest.TestCase):
 def test_explicit_neutrino_message_path(self):
  s=(ROOT/'native/guest_query.c').read_text()
  for call in ('ChannelCreate(', 'MsgReceive(', 'MsgSend(', 'MsgReply(', 'ConnectAttach(', 'ChannelDestroy(', 'TimerTimeout('):self.assertIn(call,s)
  self.assertIn('ESRCH',s)
  self.assertIn('m.replacement==target',s)
  self.assertIn('m.replacement==mainpid',s)
  self.assertIn('process snapshots',s)
 def test_build_and_capture_same_run(self):
  s=(ROOT/'tools/build_native_recorder.sh').read_text()
  self.assertIn('native/guest_query.c',s);self.assertIn('guest_query=$CAN_OUT/guest_query',s)
  subprocess.run(['bash','-n',str(ROOT/'tools/build_native_recorder.sh')],check=True)
  s=(ROOT/'tools/collect_native_incident.py').read_text()
  self.assertLess(s.index('guest_query serve'),s.index('for number in range'))
  self.assertIn('guest_query publish',s);self.assertIn('guest-query.txt',s)
  self.assertIn('no continuous',s.replace('not continuous','no continuous'))
