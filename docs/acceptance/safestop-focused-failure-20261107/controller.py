import sys,os,time,json,re,subprocess,selectors,hashlib,fcntl,socket,struct
from pathlib import Path
sys.path.insert(0,"/home/ubuntu/.openclaw/workspace/apps/canopy-qnx/tools")
from native_can_three import assert_caps,parse_qnx,require_exact
out=Path("/home/ubuntu/.openclaw/workspace/.openclaw/tmp/qnx-followup11/c6-native-h");out.mkdir(exist_ok=True)
lock=open("/home/ubuntu/qnx-host/native-test.lock","w");fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
caps=assert_caps();image=Path("/home/ubuntu/qnx-host/guest/shared/canopy-native11/ifs-native11.bin")
assert image.is_file()
args=["qemu-system-x86_64","-machine","pc","-accel","tcg,tb-size=64","-cpu","max","-smp","1","-m","512","-display","none","-serial","stdio","-monitor","none","-no-reboot","-kernel",str(image),"-drive","file=/home/ubuntu/qnx-host/guest/shared/qnx-native/disk-edu-libc,format=raw,if=ide,snapshot=on","-netdev","user,id=net0","-device","virtio-net-pci,netdev=net0,vectors=0","-object","can-bus,id=canbus0","-device","kvaser_pci,canbus=canbus0","-device","edu,dma_mask=0xffffffff"]
qpath=out/"qtest.sock"
if qpath.exists():raise RuntimeError("existing qtest socket; inspect owner")
args += ["-qtest","unix:"+str(qpath)+",server=on,wait=off","-object","can-host-socketcan,id=hostcan0,if=vcan1,canbus=canbus0"]
capture=socket.socket(socket.PF_CAN,socket.SOCK_RAW,socket.CAN_RAW);capture.bind(("vcan1",));capture.setblocking(False);frames=[]
r=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);sel=selectors.DefaultSelector();sel.register(r.stdout,selectors.EVENT_READ);serial=bytearray();report={"caps":caps,"qemu_pid":r.pid,"image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),"label":"observed in this QEMU run; app budget, not QNX benchmark","restarts":[],"success":False,"ssh_authenticated_continuity":"UNVERIFIED"}
from canopy_host.protocol import crc8
fault_observed=False
heartbeats_seen=[]
def marker(event,**extra):
 with (out/'functional-events.jsonl').open('a') as stream:
  stream.write(json.dumps(dict(scenario=tag,event=event,monotonic_ns=time.monotonic_ns(),**extra))+chr(10))
def drain():
 global fault_observed
 while True:
  try:raw=capture.recv(16)
  except BlockingIOError:break
  cid,dlc,payload=struct.unpack('=IB3x8s',raw);payload=payload[:dlc];frames.append((cid,payload.hex()))
  if cid==0x200 and 'tag' in globals() and fault in ('bad-crc','frozen') and not fault_observed:
   bad=(fault=='bad-crc' and len(payload)==4 and crc8(bytes((2,0))+payload[:3])!=payload[3])
   frozen=(fault=='frozen' and bool(heartbeats_seen) and payload==heartbeats_seen[-1])
   if bad or frozen:
    marker('fault-start');fault_observed=True
   heartbeats_seen.append(payload)
def until(marker,timeout=90):
 start=len(serial);end=time.monotonic()+timeout
 while time.monotonic()<end:
  drain()
  if sel.select(.05):
   chunk=os.read(r.stdout.fileno(),65536)
   if not chunk:raise RuntimeError("guest exited")
   serial.extend(chunk);(out/"serial.txt").write_bytes(serial)
  if marker.encode() in bytes(serial[start:]).replace(bytes([13]),b"").split(bytes([10])):return bytes(serial[start:]).decode(errors="replace")
  if r.poll() is not None:raise RuntimeError("guest died")
 raise TimeoutError(marker)
def command(text,marker):
 for pos in range(0,len(text)+1,96):
  chunk=(text+chr(10)).encode()[pos:pos+96]
  if chunk:r.stdin.write(chunk);r.stdin.flush();time.sleep(.02)
 return until(marker)
def pid(text,name):
 values=re.findall(r"^\s*(\d+)\s+[^\n]*"+re.escape(name)+r"[^\n]*$",text,re.M)
 if len(set(values))!=1:raise RuntimeError("ambiguous process identity "+name+": "+str(values))
 return int(values[0])
def traffic(number):
 command("/proc/boot/candump -u0,rx0 > /tmp/c3rx 2>&1 & RX=$!; sleep 1; echo RX_READY","RX_READY")
 time.sleep(.3);drain();frames.clear()
 gen=subprocess.Popen(["cangen","vcan1","-n","100","-I","i","-L","8","-D","i","-g","30"])
 end=time.monotonic()+15
 while gen.poll() is None and time.monotonic()<end:drain();time.sleep(.01)
 if gen.poll() is None:gen.kill();gen.wait();raise RuntimeError("cangen timeout")
 if gen.returncode:raise RuntimeError("cangen failure")
 time.sleep(.3);drain();host=list(frames)
 text=command("kill -INT $RX; wait $RX; cat /tmp/c3rx; echo RX_DONE","RX_DONE");native=parse_qnx(text);require_exact(host,native)
 expected=[(0x400+i,bytes((i*17+j*29+number)%256 for j in range(8)).hex()) for i in range(100)]
 frames.clear();r.stdin.write(b"cat > /tmp/c3tx.sh <<'C3_SCRIPT'\n");r.stdin.flush();time.sleep(.1)
 for cid,payload in expected:
  r.stdin.write((f"/proc/boot/cansend -u0,tx0 -m0x{cid:x},0,0x{payload} || exit 1\nsleep 0.03\n").encode());r.stdin.flush()
  end=time.monotonic()+.1
  while time.monotonic()<end:
   if sel.select(.01):serial.extend(os.read(r.stdout.fileno(),65536))
   drain()
 r.stdin.write(b"C3_SCRIPT\n");r.stdin.flush();time.sleep(.1)
 text=command("sh /tmp/c3tx.sh; echo C3_TX_RC=$?; echo TX_DONE","TX_DONE");time.sleep(.3);drain()
 assert "C3_TX_RC=0" in text.replace(chr(13),"").splitlines();require_exact(expected,frames)
 detail={"run":number,"host_rx":host,"qnx_rx":native,"native_tx_expected":expected,"host_tx":list(frames),"ordered_byte_exact":True}
 (out/("traffic"+str(number)+".json")).write_text(json.dumps(detail,indent=2));print("POST_RESTART_RX100_TX100_EXACT "+str(number),flush=True)
 return {"rx_host":len(host),"rx_qnx":len(native),"tx_expected":len(expected),"tx_host":len(frames),"ordered_byte_exact":True}
try:
 until("CANOPY_SLM_IMAGE_READY",100)
 maintext=command("pidin ar; echo MAIN_PID_OBSERVED","MAIN_PID_OBSERVED");mainpid=pid(maintext,'io-sock')
 mainirqtext=command('pidin -p '+str(mainpid)+' irqs; echo MAIN_IRQ_OBSERVED','MAIN_IRQ_OBSERVED')
 (out/'main-irq-before.txt').write_text(mainirqtext)
 qt=socket.socket(socket.AF_UNIX);qt.settimeout(3);qt.connect(str(qpath));f=qt.makefile("rwb",buffering=0)
 def pci(addr,value=None):
  def call(x):
   f.write((x+chr(10)).encode());row=f.readline().decode().strip()
   if not row.startswith("OK"):raise RuntimeError(row)
   return row
  call("outl 0xcf8 "+hex(addr))
  return int(call("inl 0xcfc").split()[-1],16) if value is None else call("outl 0xcfc "+hex(value))
 devices=[{"slot":i,"id":pci(0x80000000+(i<<11)),"irq":pci(0x8000003c+(i<<11))} for i in range(1,8)]
 report["pci_devices"]=devices
 kvaser=next(d for d in devices if d["id"]==0x840610e8)
 pin=((kvaser["irq"]>>8)&255)-1;route=(kvaser["slot"]-1+pin)%4;irq=10 # experimentally required by existing libcan path; PCI line is recorded separately
 old=pci(0x80000860);new=(old&~(255<<(8*route)))|(irq<<(8*route));new=(new&~(255<<16))|(10<<16);pci(0x80000860,new);assert pci(0x80000860)==new
 report["routing"]={"original":old,"updated":new,"pirq_index":route,"irq":irq,"only_kvaser_route_changed":False,"main_route_to_previously_observed_irq10":True};f.close();qt.close()
 command('cat > /dev/shmem/slm-can-safestop.xml <<\'C6_XML\'\n<!-- Original C6 demo profile. CAN IRQ service must outrank FIFO20 consumer.\nParser/runtime acceptance must be observed; no production isolation claim. -->\n<SLM:system xmlns:SLM="urn:canopy:slm">\n  <SLM:component name="canopy-can">\n    <SLM:command>/proc/boot/dev-can-linux</SLM:command>\n    <SLM:args>-b id=0,freq=500k</SLM:args>\n    <SLM:priority>24r</SLM:priority>\n    <SLM:repair backoff="1">restart</SLM:repair>\n    <SLM:stop stop="signal" child="false" timeout="2000">SIGTERM</SLM:stop>\n  </SLM:component>\n</SLM:system>\nC6_XML\necho C6_PROFILE_STAGED',"C6_PROFILE_STAGED")
 command("/proc/boot/slm -V -n /dev/slm-canopy -R 5/min -s canopy-can /dev/shmem/slm-can-safestop.xml > /tmp/slm.log 2>&1 & sleep 3; ls /dev/can0/rx0; pidin ar; echo CAN_READY","CAN_READY")
 can=command('pidin ar; echo CAN_PID_OBSERVED','CAN_PID_OBSERVED');canpid=pid(can,'dev-can-linux')
 detail=command('pidin -p '+str(canpid)+' sched; pidin -p '+str(canpid)+' irqs; cat /tmp/slm.log; echo CAN_IRQ_OBSERVED','CAN_IRQ_OBSERVED')
 (out/'can-irq-scheduler-before.txt').write_text(detail)
 qt=socket.socket(socket.AF_UNIX);qt.settimeout(3);qt.connect(str(qpath));f=qt.makefile('rwb',buffering=0)
 after=pci(0x80000860);report['pirq_after_driver_start']=after
 if after!=new:pci(0x80000860,new)
 report['pirq_final']=pci(0x80000860);f.close();qt.close()
 report['preflight_traffic']=traffic(0)
 diag=command("ls /proc/boot/on /system/bin/on /usr/bin/on; echo C6_ON_DIAG","C6_ON_DIAG")
 controls=[x.strip() for x in diag.replace(chr(13),"").splitlines() if x.strip() in ("/proc/boot/on","/system/bin/on","/usr/bin/on")]
 if not controls:raise RuntimeError("native priority launcher absent")
 command(controls[0]+" -p30f /bin/sh -c 'echo C6_CONTROL_READY; exec /bin/sh'","C6_CONTROL_READY")
 repo="/home/ubuntu/.openclaw/workspace/apps/canopy-qnx"
 env=dict(os.environ,PYTHONPATH=repo)
 report["scenarios"]=[]
 report["source_sha256"]={name:hashlib.sha256((Path(repo)/name).read_bytes()).hexdigest() for name in ['native/safestop_qnx.c','safety/native_inputs.c','safety/safestop.c','config/supervision/slm-can-safestop.xml']}
 (out/'functional-events.jsonl').write_text('')
 for scenario,fault in [("healthy","none"),("stale","none"),("healthy","bad-crc"),("healthy","frozen"),("kill","none"),("kill-resume","none")]:
  tag=scenario+"-"+fault;frames.clear();heartbeats_seen.clear();fault_observed=False;start=time.monotonic()
  ecu=subprocess.Popen(["python3",repo+"/tools/native_safestop_host.py","ecu","--interface","vcan1","--duration","11","--output",str(out/(tag+"-ecu.jsonl"))],env=env)
  stim=subprocess.Popen(["python3",repo+"/tools/native_safestop_host.py","stimulus","--interface","vcan1","--duration","11","--scenario",scenario if scenario in ("healthy","stale") else "healthy","--events",str(out/"functional-events.jsonl")],env=env)
  command("/proc/boot/safestop-qnx 850 "+fault+" > /dev/shmem/c6.log 2>&1 & C6=$!; echo C6_STARTED","C6_STARTED")
  observed=command("/proc/boot/sleep 0.5; pidin ar; pidin -p $C6 threads; pidin -p $C6 sched; cat /dev/shmem/c6.log | head -2; echo C6_SCHED","C6_SCHED")
  cs=command('pidin -p '+str(canpid)+' sched; command -v slay; echo QUEUE_THREAD_DIAG','QUEUE_THREAD_DIAG')
  low=re.findall(r'^\s*'+str(canpid)+r'\s+(\d+)\s+[^\n]*\s(?:10|20)r\s',cs,re.M)
  paths=[line.strip() for line in cs.replace(chr(13),'').splitlines() if line.strip().startswith('/') and line.strip().endswith('/slay')]
  if low and not paths:raise RuntimeError('observed helper adjustment requested but native slay absent')
  if low:
   update='; '.join(paths[0]+' -m pid -P24r -T '+tid+' '+str(canpid) for tid in low)
   cs+=command(update+'; pidin -p '+str(canpid)+' sched; echo QUEUE_THREAD_ADJUSTED','QUEUE_THREAD_ADJUSTED')
  (out/(tag+'-can-workers.txt')).write_text(cs)
  report.setdefault('experimental_helper_priority_adjustments',[]).append(dict(scenario=tag,can_pid=canpid,tids=low,priority='24r',mechanism='documented slay debug scheduling; not production configuration'))
  owned=pid(observed,'safestop-qnx');marker('native-start',pid=owned)
  (out/(tag+'-scheduler.txt')).write_text(observed)
  if not re.search(r'\b20f\b',observed):raise RuntimeError('independent pidin FIFO20 evidence missing')
  if 'C6_READY timer=CLOCK_MONOTONIC interval_ns=10000000' not in observed:raise RuntimeError('native timer setup marker missing')
  marker('native-pulse-proof',pid=owned,policy='SCHED_FIFO',priority=20,mechanism='CLOCK_MONOTONIC/MsgReceivePulse',interval_ns=10000000)
  killed=None;restarted=None;prior_native=''
  while time.monotonic()-start<11.5:
   drain()
   if scenario in ("kill","kill-resume") and killed is None and time.monotonic()-start>3:
    text=command("pidin ar; echo C6_PID_CHECK","C6_PID_CHECK");owned=pid(text,"safestop-qnx")
    marker('fault-start')
    command("kill -9 "+str(owned)+"; echo C6_KILLED","C6_KILLED");killed=owned
    marker('process-killed',pid=owned,signal=9)
   if scenario=='kill-resume' and killed is not None and restarted is None and time.monotonic()-start>6:
    prior_native=command('cat /dev/shmem/c6.log; echo KILLED_NATIVE_LOG','KILLED_NATIVE_LOG')
    command('/proc/boot/safestop-qnx 300 none > /dev/shmem/c6.log 2>&1 & C6=$!; echo C6_RESTARTED','C6_RESTARTED')
    observed=command('/proc/boot/sleep 0.5; pidin ar; pidin -p $C6 threads; echo C6_RESTART_PID','C6_RESTART_PID');restarted=pid(observed,'safestop-qnx')
    if not re.search(r'\b20f\b',observed):raise RuntimeError('restart independent FIFO20 proof absent')
    marker('native-restart',pid=restarted);(out/(tag+'-restart-scheduler.txt')).write_text(observed)
   time.sleep(.01)
  ecu.wait(5);stim.wait(5);assert ecu.returncode==0 and stim.returncode==0
  text=command("wait $C6; cat /dev/shmem/c6.log; echo C6_COLLECTED","C6_COLLECTED")
  text=prior_native+text
  (out/(tag+"-native.txt")).write_text(text)
  heartbeat=[(cid,payload) for cid,payload in frames if cid==0x200]
  (out/(tag+"-host-frames.json")).write_text(json.dumps(heartbeat,indent=2))
  native=re.findall(r"C6_TICK[^\n]*payload=([0-9a-f]{8})",text)
  assert "C6_FIFO" in text and "C6_READY" in text and native, "native FIFO/pulse proof missing"
  assert [x[1] for x in heartbeat]==native,"native/host heartbeat mismatch"
  rows=[json.loads(row) for row in (out/(tag+"-ecu.jsonl")).read_text().splitlines()]
  samples=[row for row in rows if row["event"]=="actuator"]
  assert samples and any(row["speed_mps"]==0 for row in samples),"simulated actuator stop unobserved"
  report["scenarios"].append(dict(scenario=scenario,fault=fault,heartbeats=len(heartbeat),byte_exact=True,native_fifo_pulses=True,killed_pid=killed,restarted_pid=restarted,ecu_stopped=True))
  print("C6_SCENARIO_OBSERVED "+json.dumps(report["scenarios"][-1]),flush=True)
 report["observations_collected"]=True
 report["success"]=False
 report["gate_status"]="NOT ACCEPTED until independent functional validation; these are raw runtime observations"
except Exception as error:
 try:
  failed=command("cat /dev/shmem/c6.log; pidin ar; echo C6_FAILURE_DIAG","C6_FAILURE_DIAG");(out/"failure-native.txt").write_text(failed)
 except Exception:pass
 report["error"]=str(error);print("C6_NATIVE_FAIL "+str(error),flush=True)
finally:
 r.terminate()
 try:r.wait(10)
 except subprocess.TimeoutExpired:r.kill();r.wait()
 for name in ['ecu','stim']:
  child=globals().get(name)
  if child is not None and child.poll() is None:
   child.terminate()
   try:child.wait(5)
   except subprocess.TimeoutExpired:child.kill();child.wait()
 capture.close();qpath.unlink(missing_ok=True);report["guest_stopped_reaped"]=True;(out/"receipt.json").write_text(json.dumps(report,indent=2)+chr(10));(out/"serial.txt").write_bytes(serial);print(json.dumps(report),flush=True)
sys.exit(0 if report.get("observations_collected") else 1)
