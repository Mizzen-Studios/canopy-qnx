import unittest,os,pty,subprocess,select,time,uuid,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
import importlib.util
_spec=importlib.util.spec_from_file_location('canopy_recording_transport',Path(__file__).resolve().parents[2]/'tools/recording_transport/__init__.py')
_module=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_module);transfer=_module.transfer
class Transport(unittest.TestCase):
 def trial(self,payload,fault=None,delay=0):
  master,slave=pty.openpty();p=subprocess.Popen(['/bin/sh','-i'],stdin=slave,stdout=slave,stderr=slave,env={**os.environ,'PS1':'','PS2':''},start_new_session=True);os.close(slave)
  dest='/tmp/rt-host-'+uuid.uuid4().hex;logs=[];count=0
  def exchange(wire,marker,timeout):
   nonlocal count
   count+=1
   if fault=='truncate' and count==2:wire=wire[:12]+b'\n'
   if delay:time.sleep(delay)
   offset=0
   while offset<len(wire):offset+=os.write(master,wire[offset:offset+7])
   end=time.monotonic()+min(timeout,.3 if fault else 3);raw=b''
   while time.monotonic()<end:
    if select.select([master],[],[],.02)[0]:raw+=os.read(master,65536)
    if marker in raw.replace(b'\r',b'').split(b'\n'):
     if fault=='lostack':return wire
     if fault=='corrupt' and count==2:Path(dest).write_bytes(b'CORRUPTED')
     if fault=='timeout':raise TimeoutError('injected timeout')
     return raw
   raise TimeoutError('ack timeout')
  try:
   result=transfer(payload,dest,exchange,logs.append,toolbox='HOST_TEST',timeout=.4)
   self.assertEqual(Path(dest).read_bytes(),payload);self.assertTrue(result['verified_before_execution']);self.assertTrue(logs);return result
  finally:
   p.kill();p.wait(3);os.close(master);Path(dest).unlink(missing_ok=True)
 def test_bytes_quotes_control_boundaries(self):self.trial(bytes(range(256))+b"'\\\n\r$()\x00"+b'x'*100)
 def test_backpressure(self):self.trial(b'bounded host PTY bytes'*4,delay=.01)
 def test_faults(self):
  for f in ['truncate','lostack','corrupt','timeout']:
   with self.subTest(f=f),self.assertRaises((RuntimeError,TimeoutError)):self.trial(b'abcdef0123456789',f)
 def test_bad_destination(self):
  with self.assertRaises(ValueError):transfer(b'x','/tmp/x;echo bad',None,None)
if __name__=='__main__':unittest.main()
