#!/usr/bin/env python3
"""Private target gate; intentionally fixes legacy PIIX IRQ routing for this image.
Invoke ONLY via scripts/qemu-capped.sh. Requires external licensed image and GPL tools.
No SDK, third-party driver, or target image is redistributed here.
"""
import subprocess,pathlib,time,selectors,os,sys,socket,struct,threading,json
if len(sys.argv)!=4: raise SystemExit('Run via scripts/qemu-capped.sh: qnx_can_gate.py IMAGE_DIR LABEL END_MARKER')
p=pathlib.Path(sys.argv[1]).resolve();label=sys.argv[2];marker=sys.argv[3].encode()
if not label.replace('-','').replace('_','').isalnum(): raise SystemExit('invalid label')
if (p/'can-gate.sock').exists(): raise SystemExit('socket already exists; inspect active probe before retry')
args=['qemu-system-x86_64','-machine','pc,accel=tcg','-cpu','max','-smp','1','-m','512','-display','none','-serial','stdio','-monitor','none','-no-reboot','-kernel',str(p/'ifs.bin'),'-drive','file='+str(p/'disk-qemu')+',format=raw,if=ide','-nic','user,model=virtio-net-pci','-object','can-bus,id=canbus0','-device','kvaser_pci,canbus=canbus0','-device','edu,dma_mask=0xffffffff']
args+=['-qtest','unix:'+str(p/'can-gate.sock')+',server=on,wait=off','-qtest-log',str(p/(label+'-qtest.log'))]
args+=['-object','can-host-socketcan,id=hostcan0,if=vcan1,canbus=canbus0']
can=socket.socket(socket.PF_CAN,socket.SOCK_RAW,socket.CAN_RAW);can.bind(('vcan1',));can.setblocking(False);received=[];sent=False
r=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);sel=selectors.DefaultSelector();sel.register(r.stdout,selectors.EVENT_READ);end=time.monotonic()+180;buf=b''
try:
 with (p/(label+'.log')).open('wb') as f:
  while time.monotonic()<end:
   if sel.select(.05):
    b=os.read(r.stdout.fileno(),65536)
    if not b:break
    f.write(b);f.flush();buf+=b
    if b'QNX_RX_READY' in buf and not sent:
     sent=True
     q=socket.socket(socket.AF_UNIX);q.settimeout(3);q.connect(str(p/'can-gate.sock'));qf=q.makefile('rwb',buffering=0)
     def qt(cmd):
      qf.write((cmd+'\n').encode());return qf.readline().decode().strip()
     for dev in range(32):
      qt('outl 0xcf8 '+hex(0x80000000+(dev<<11)))
      if '840610e8' in qt('inl 0xcfc').lower():
       print('KVASER_SLOT',dev,flush=True)
       for off in (4,0x10,0x14,0x18,0x3c):
        qt('outl 0xcf8 '+hex(0x80000000+(dev<<11)+off));print('CFG',hex(off),qt('inl 0xcfc'),flush=True)
     for port in [0xc038,0xc080,0xc082,0xc084,0xc086,0xc087,0xc09f]:
      print('REG',hex(port),qt(('inl' if port==0xc038 else 'inb')+' '+hex(port)),flush=True)

     print('PIRQ_BEFORE',qt('outl 0xcf8 0x80000860'),qt('inl 0xcfc'),flush=True)
     print('PIRQ_ROUTE_TO_QNX_IRQ10',qt('outl 0xcfc 0x0a0a0a0a'),flush=True)
     time.sleep(.3)
     def send():
      for i in range(100):
       can.send(struct.pack('=IB3x8s',0x123,8,bytes.fromhex('0102030405060708')));time.sleep(.03)
      time.sleep(.2)
      for port in [0xc038,0xc080,0xc082,0xc084,0xc09d,0xc09e]:
       print('AFTER_RX',hex(port),qt(('inl' if port==0xc038 else 'inb')+' '+hex(port)),flush=True)
     threading.Thread(target=send).start()
    if marker in buf:
     time.sleep(.1)
     try:
      while True:
       frame=can.recv(16);cid,n,data=struct.unpack("=IB3x8s",frame)
       if cid==0x321:received.append(data[:n].hex())
     except BlockingIOError:pass
     break
   try:
    while True:
     frame=can.recv(16);cid,n,data=struct.unpack('=IB3x8s',frame)
     if cid==0x321:received.append(data[:n].hex())
   except BlockingIOError:pass
   if r.poll() is not None:break
finally:
 r.terminate()
 try:r.wait(10)
 except subprocess.TimeoutExpired:r.kill();r.wait()
print(buf.decode(errors='replace')[-16000:]);print('gate completed:',marker in buf)

rows=[line for line in buf.decode(errors='replace').splitlines() if '/dev/can0/rx0 TS:' in line]
result={'hostTx':100 if sent else 0,'qnxRx':len(rows),'qnxRxByteExact':bool(rows) and all('[SFF] 123 [8] 01 02 03 04 05 06 07 08' in line for line in rows),'qnxTxReceived':len(received),'qnxTxByteExact':bool(received) and all(x=='1122334455667788' for x in received),'marker':marker in buf,'routingOverride':'PIIX PIRQ A-D -> IRQ10; experimental QNX legacy board mapping correction','hostFrameIntervalSeconds':.03}
(p/(label+'-results.json')).write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['hostTx']==result['qnxRx']==result['qnxTxReceived']==100 and result['qnxRxByteExact'] and result['qnxTxByteExact'] and result['marker'] else 1)
