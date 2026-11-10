#!/usr/bin/env python3
import sys,os,time,json,re,subprocess,selectors,hashlib,fcntl,socket,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from native_can_three import assert_caps,parse_qnx,require_exact
import argparse,uuid
ap=argparse.ArgumentParser(description="Bounded QNX libcan incident")
for n in ('image','disk','out','lock'):ap.add_argument('--'+n,required=True,type=Path)
ap.add_argument('--interface',default='vcan1')
a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
lock=open(a.lock,'a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
caps=assert_caps();image=a.image.resolve()
args=["qemu-system-x86_64","-machine","pc,accel=tcg","-cpu","max","-smp","1","-m","512","-display","none","-serial","stdio","-monitor","none","-no-reboot","-kernel",str(image),"-drive",f"file={a.disk.resolve()},format=raw,if=ide,snapshot=on","-nic","user,model=virtio-net-pci","-object","can-bus,id=canbus0","-device","kvaser_pci,canbus=canbus0","-device","edu,dma_mask=0xffffffff"]
qpath=out/"qtest.sock"
if qpath.exists():raise RuntimeError("existing qtest socket; inspect owner")
args += ["-qtest","unix:"+str(qpath)+",server=on,wait=off","-object","can-host-socketcan,id=hostcan0,if="+a.interface+",canbus=canbus0"]
capture=socket.socket(socket.PF_CAN,socket.SOCK_RAW,socket.CAN_RAW);capture.bind((a.interface,));capture.setblocking(False);frames=[]
r=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);sel=selectors.DefaultSelector();sel.register(r.stdout,selectors.EVENT_READ);serial=bytearray();report={"caps":caps,"qemu_pid":r.pid,"collector_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),"qemu_command":args,"image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),"label":"observed in this QEMU run; app budget, not QNX benchmark","run_id":"native-"+uuid.uuid4().hex,"captured_at":time.time(),"disk_sha256":hashlib.sha256(a.disk.read_bytes()).hexdigest(),"restarts":[],"success":False,"ssh_authenticated_continuity":"UNVERIFIED"}
def drain():
 while True:
  try:raw=capture.recv(16)
  except BlockingIOError:break
  cid,dlc,payload=struct.unpack("=IB3x8s",raw);frames.append((cid,payload[:dlc].hex()))
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
 gen=subprocess.Popen(["cangen",a.interface,"-n","100","-I","i","-L","8","-D","i","-g","30"])
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
 old=pci(0x80000860);new=(old&~(255<<(8*route)))|(irq<<(8*route));pci(0x80000860,new);assert pci(0x80000860)==new
 report["routing"]={"original":old,"updated":new,"pirq_index":route,"irq":irq,"only_kvaser_route_changed":True};f.close();qt.close()
 baseline=command("pidin ar; echo BASE_DONE","BASE_DONE");mainpid=pid(baseline,"io-sock");report["main_io_sock_pid"]=mainpid
 text=command("/proc/boot/slm -V -n /dev/slm-canopy -R 5/min -s canopy-can /proc/boot/slm-can-fallback.xml > /tmp/slm.log 2>&1 & sleep 3; cat /tmp/slm.log; /proc/boot/slmctl -n /dev/slm-canopy 'listall -v'; pidin ar; echo SLM_START_DONE","SLM_START_DONE")
 (out/"startup.txt").write_text(text);print(text,flush=True);current=pid(text,"dev-can-linux")
 query_start=command("/proc/boot/guest_query serve "+str(current)+" "+str(mainpid)+" > /tmp/query-service.log 2>&1 & QUERY=$!; sleep 1; cat /tmp/query-service.log; echo QUERY_START_DONE","QUERY_START_DONE")
 assert "CANOPY_QUERY_READY" in query_start
 report["guest_query_server_pid"]=int(query_start.split("CANOPY_QUERY_READY pid=",1)[1].split()[0])
 for number in range(1,2):
  check=command("pidin ar; echo ID_CHECK","ID_CHECK");assert pid(check,"dev-can-linux")==current and pid(check,"io-sock")==mainpid and current!=mainpid
  start=time.monotonic();text=command("/proc/boot/incident_recorder "+str(current)+"; echo RECORDER_RC=$?; sleep 3; /proc/boot/slmctl -n /dev/slm-canopy 'active -v'; pidin ar; ls /dev/can0/rx0; echo RESTART_DONE","RESTART_DONE")
  (out/"restart.txt").write_text(text)
  new=pid(text,"dev-can-linux");assert new!=current and pid(text,"io-sock")==mainpid
  assert "/dev/can0/rx0" in text and "No such file" not in text
  report["restarts"].append({"run":number,"killed_pid":current,"new_pid":new,"main_pid_unchanged":True,"observed_seconds_including_fixed_3s_settle":time.monotonic()-start});current=new;print("NATIVE_SLM_RESTART_PASS "+str(number),flush=True)
  report["restarts"][-1]["traffic"]=traffic(number)
  query=command("/proc/boot/guest_query publish "+str(new)+"; echo QUERY_PUBLISH_RC=$?; for q in killed recovery survivors isolation; do /proc/boot/guest_query $q; echo QUERY_RC=$?; done; echo QUERY_DONE","QUERY_DONE")
  records=[json.loads(line.split("CANOPY_GUEST_QUERY ",1)[1]) for line in query.replace(chr(13),"").splitlines() if line.startswith("CANOPY_GUEST_QUERY ")]
  assert len(records)==5 and [x["query"] for x in records]==["publish","killed","recovery","survivors","isolation"]
  assert all(x["server"]==report["guest_query_server_pid"] and x["target"]==report["restarts"][-1]["killed_pid"] and x["replacement"]==new and x["main"]==mainpid and x["killed"]==x["recovery"]==x["survivor"]==1 for x in records)
  assert query.count("QUERY_RC=0")==4 and "QUERY_PUBLISH_RC=0" in query
  (out/"guest-query.txt").write_text(query);report["guest_query"]={"status":"PASS","rows":records,"sha256":hashlib.sha256(query.encode()).hexdigest(),"scope":"process snapshots, not continuous availability or adversarial isolation"}
 control=command("/proc/boot/prereq_containment; echo CONTROL_RC=$?; /proc/boot/ability_lesson deny; echo ABILITY_DENY_RC=$?; /proc/boot/ability_lesson allow; echo ABILITY_ALLOW_RC=$?; /proc/boot/slog2info -b canopy_incident -f -S -t; echo NATIVE_CAPTURE_DONE","NATIVE_CAPTURE_DONE")
 (out/"control-slog.txt").write_text(control)
 report["success"]=True
except Exception as error:
 report["error"]=str(error);print("NATIVE_SLM_FAIL "+str(error),flush=True)
finally:
 r.terminate()
 try:r.wait(10)
 except subprocess.TimeoutExpired:r.kill();r.wait()
 capture.close();qpath.unlink(missing_ok=True);report["guest_stopped_reaped"]=True;report["raw_sha256"]=hashlib.sha256(serial).hexdigest();(out/"receipt.json").write_text(json.dumps(report,indent=2)+chr(10));(out/"serial.txt").write_bytes(serial);print(json.dumps(report),flush=True)
sys.exit(0 if report["success"] else 1)
