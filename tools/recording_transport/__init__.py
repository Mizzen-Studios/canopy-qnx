"""Acknowledged shell transfer; never executes transferred contents or retries."""
import base64,hashlib,re,time,uuid

def transfer(payload,destination,exchange,log,*,nonce=None,chunk_bytes=8,timeout=4,toolbox='/proc/boot/toybox'):
 if not re.fullmatch(r'/tmp/[A-Za-z0-9_.-]+',destination):raise ValueError('unsafe destination')
 if not 1<=chunk_bytes<=8:raise ValueError('chunk bound')
 if toolbox not in ['/proc/boot/toybox','HOST_TEST']:raise ValueError('toolbox')
 prefix='' if toolbox=='HOST_TEST' else toolbox+' '
 nonce=nonce or uuid.uuid4().hex
 if not re.fullmatch('[a-f0-9]{32}',nonce):raise ValueError('nonce')
 seq=0
 def request(body,expected):
  nonlocal seq
  marker='RT_'+nonce+'_'+str(seq)
  command=body+" && printf '\nRT_%s_%s\n' '"+nonce+"' '"+str(seq)+"'"
  wire=(command+'\n').encode();started=time.monotonic_ns()
  try:reply=exchange(wire,marker.encode(),timeout)
  except Exception as error:
   log({'seq':seq,'write_b64':base64.b64encode(wire).decode(),'start_mono_ns':started,'end_mono_ns':time.monotonic_ns(),'error':str(error)});raise
  log({'seq':seq,'write_b64':base64.b64encode(wire).decode(),'reply_b64':base64.b64encode(reply).decode(),'start_mono_ns':started,'end_mono_ns':time.monotonic_ns()})
  lines=reply.replace(b'\r',b'').split(b'\n')
  if lines.count(marker.encode())!=1:raise RuntimeError('missing/duplicate standalone ack '+str(seq))
  if expected and not expected(lines):raise RuntimeError('guest integrity mismatch '+str(seq))
  seq+=1
 request(': > '+destination,None)
 for i in range(0,len(payload),chunk_bytes):
  b=payload[i:i+chunk_bytes];octal=''.join('\\%03o'%x for x in b)
  request("printf '"+octal+"' >> "+destination,None)
 digest=hashlib.sha256(payload).hexdigest();length=len(payload)
 body='RT_H=$('+prefix+'sha256sum '+destination+') && RT_N=$('+prefix+'wc -c < '+destination+') && printf \'\nRT_HASH %s\nRT_SIZE %s\n\' "$RT_H" "$RT_N"'
 request(body,lambda lines:sum(bool(re.fullmatch(rb'RT_HASH '+digest.encode()+rb'  .+',x)) for x in lines)==1 and sum(bool(re.fullmatch(rb'RT_SIZE\s+'+str(length).encode(),x)) for x in lines)==1)
 return {'bytes':length,'sha256':digest,'acks':seq,'verified_before_execution':True,'nonce':nonce}
