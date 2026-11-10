"""One existing-key SSH connection, two unpredictable challenges. No server repair."""
import os, selectors, subprocess, time, uuid, hashlib
from pathlib import Path
class Continuity:
 def __init__(self, port, key, out):
  self.process=None;self.before=None;self.out=out;self.stream=bytearray();self.detail={'status':'UNVERIFIED','scope':'same connection challenge observations only; no availability guarantee'}
  self.log=open(out/'ssh-client.log','wb')
  try:
   if not Path(key).is_file():raise RuntimeError('existing test identity unavailable')
   self.process=subprocess.Popen(['ssh','-T','-i',str(key),'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=accept-new','-o','UserKnownHostsFile='+str(out/'ssh-known-hosts'),'-o','ConnectTimeout=10','-o','ConnectionAttempts=1','-o','ControlMaster=no','-o','ControlPath=none','-o','ServerAliveInterval=2','-o','ServerAliveCountMax=3','-p',str(port),'root@127.0.0.1','sh'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log)
   self.select=selectors.DefaultSelector();self.select.register(self.process.stdout,selectors.EVENT_READ)
   self.before=self.challenge('before')
  except Exception as e:self.detail['reason']=str(e)
 def challenge(self,phase):
  if self.process is None or self.process.poll() is not None:raise RuntimeError('SSH connection not active')
  token='CANOPY_SSH_'+uuid.uuid4().hex
  self.process.stdin.write(('echo '+token+'; echo SSH_SHELL_PID=$$'+chr(10)).encode());self.process.stdin.flush()
  end=time.monotonic()+15;start=len(self.stream)
  while time.monotonic()<end:
   if self.select.select(.1):
    row=os.read(self.process.stdout.fileno(),4096)
    if not row:raise RuntimeError('SSH EOF')
    self.stream.extend(row);(self.out/'ssh-stream.txt').write_bytes(self.stream)
   lines=bytes(self.stream[start:]).replace(bytes([13]),b'').splitlines()
   if token.encode() in lines and any(x.startswith(b'SSH_SHELL_PID=') for x in lines):
    pid=next(x.decode().split('=')[1] for x in lines if x.startswith(b'SSH_SHELL_PID='))
    return {'phase':phase,'challenge':token,'response_sha256':hashlib.sha256(token.encode()).hexdigest(),'shell_pid':pid,'client_pid':self.process.pid}
   if self.process.poll() is not None:raise RuntimeError('SSH client exited')
  raise RuntimeError('SSH challenge timeout')
 def finish(self):
  try:
   if not self.before:raise RuntimeError('before challenge not observed')
   after=self.challenge('after')
   if after['shell_pid']!=self.before['shell_pid']:raise RuntimeError('SSH shell changed')
   self.detail.update(status='PASS',before=self.before,after=after,single_client_single_connection=True)
  except Exception as e:self.detail.update(status='UNVERIFIED',reason=str(e))
  return self.detail
 def close(self):
  if self.process is not None:
   self.process.terminate()
   try:self.process.wait(5)
   except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
   self.select.close()
  self.log.close()
