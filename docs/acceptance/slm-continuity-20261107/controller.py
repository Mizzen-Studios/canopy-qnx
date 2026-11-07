import sys,os,time,json,re,subprocess,selectors,hashlib,fcntl,socket,struct,threading,shlex
from pathlib import Path
sys.path.insert(0,"/home/ubuntu/.openclaw/workspace/apps/canopy-qnx/tools")
from native_can_three import assert_caps,parse_qnx,require_exact
out=Path("/home/ubuntu/.openclaw/workspace/.openclaw/tmp/qnx-followup11/c3-continuity-g");out.mkdir(exist_ok=True)
lock=open("/home/ubuntu/qnx-host/native-test.lock","w");fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
caps=assert_caps();image=Path("/home/ubuntu/qnx-host/guest/shared/canopy-native11/ifs-native11.bin")
assert hashlib.sha256(image.read_bytes()).hexdigest()=="84fc4eda34654854333cf71320b375f2eedae405a3849475623c179443f616f1"
probe=socket.socket();probe.bind(("127.0.0.1",0));port=probe.getsockname()[1];probe.close()
ssh=None;ticks=[];ssh_thread=None;sshlog=open(out/"ssh-debug.txt","wb")
args=["qemu-system-x86_64","-machine","pc","-accel","tcg,tb-size=64","-cpu","max","-smp","1","-m","512","-display","none","-serial","stdio","-monitor","none","-no-reboot","-kernel",str(image),"-drive","file=/home/ubuntu/qnx-host/guest/shared/qnx-native/disk-edu-libc,format=raw,if=ide,snapshot=on","-netdev","user,id=net0,hostfwd=tcp:127.0.0.1:"+str(port)+"-:22","-device","virtio-net-pci,netdev=net0,vectors=0","-object","can-bus,id=canbus0","-device","kvaser_pci,canbus=canbus0","-device","edu,dma_mask=0xffffffff"]
qpath=out/"qtest.sock"
if qpath.exists():raise RuntimeError("existing qtest socket; inspect owner")
args += ["-qtest","unix:"+str(qpath)+",server=on,wait=off","-object","can-host-socketcan,id=hostcan0,if=vcan1,canbus=canbus0"]
capture=socket.socket(socket.PF_CAN,socket.SOCK_RAW,socket.CAN_RAW);capture.bind(("vcan1",));capture.setblocking(False);frames=[]
r=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);sel=selectors.DefaultSelector();sel.register(r.stdout,selectors.EVENT_READ);serial=bytearray();report={"caps":caps,"qemu_pid":r.pid,"image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),"label":"observed in this QEMU run; app budget, not QNX benchmark","restarts":[],"success":False,"ssh_authenticated_continuity":"UNVERIFIED"}
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
 maintext=command("pidin ar; echo IRQ_MAIN_PID","IRQ_MAIN_PID");observed_main=pid(maintext,"io-sock")
 irqtext=command("pidin -p "+str(observed_main)+" irqs; echo IRQ_MAIN_OBSERVED","IRQ_MAIN_OBSERVED")
 (out/"main-irq-before.txt").write_text(irqtext)
 irqvalues=re.findall(r"^\s+\d+\s+(0x[0-9a-f]+)\s+\d+\s+[-A-Z]+\s+=",irqtext,re.M)
 if len(irqvalues)!=1:raise RuntimeError("ambiguous main IRQ "+str(irqvalues))
 mainirq=int(irqvalues[0],16);assert mainirq in (10,11)
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
 old=pci(0x80000860);new=(old&~(255<<(8*route)))|(irq<<(8*route));new=(new&~(255<<16))|(mainirq<<16);pci(0x80000860,new);assert pci(0x80000860)==new
 report["routing"]={"original":old,"updated":new,"pirq_index":route,"irq":irq,"only_kvaser_route_changed":False,"network_route_corrected_to_observed_main_irq":mainirq,"observed_main_pid":observed_main};f.close();qt.close()
 net=command("ifconfig -a; netstat -rn; ls /proc/boot/libm.so.3 /system/lib/libm.so.3; pidin ar; echo NET_DIAG","NET_DIAG")
 (out/"network-before.txt").write_text(net)
 names=re.findall(r"^([a-zA-Z][a-zA-Z0-9]+): flags=",net,re.M)
 names=[n for n in names if n.startswith('vtnet')]
 if len(names)!=1:raise RuntimeError("No unambiguous observed main network interface: "+str(names))
 net=command("ifconfig "+names[0]+" inet 10.0.2.15 netmask 255.255.255.0 up; ifconfig "+names[0]+"; netstat -rn; echo NET_CONFIGURED","NET_CONFIGURED")
 (out/"network-configured.txt").write_text(net)
 baseline=command("pidin ar; echo BASE_DONE","BASE_DONE");mainpid=pid(baseline,"io-sock");report["main_io_sock_pid"]=mainpid
 diag=command("command -v sshd; command -v ssh-keygen; grep '^root:' /etc/passwd; echo SSH_DIAG","SSH_DIAG");(out/"ssh-diag.txt").write_text(diag)
 lines=diag.replace(chr(13),"").splitlines();sshd=next(line.strip() for line in lines if line.strip().startswith("/") and line.strip().endswith("/sshd"))
 rootline=next(line for line in lines if line.startswith("root:"));home=rootline.split(":")[5];assert home.startswith("/") and " " not in home
 pub=Path("/home/ubuntu/.openclaw/.secrets/qnx-test/id_ed25519.pub").read_text().strip()
 command("mkdir -p "+home+"/.ssh; chmod 700 "+home+"/.ssh; echo "+shlex.quote(pub)+" > "+home+"/.ssh/authorized_keys; chmod 600 "+home+"/.ssh/authorized_keys; ssh-keygen -q -t ed25519 -N '' -f /tmp/qnx11-host; echo SSH_KEYS_DONE","SSH_KEYS_DONE")
 config=["Port 22","ListenAddress 0.0.0.0","HostKey /tmp/qnx11-host","PidFile /tmp/qnx11-sshd.pid","PermitRootLogin prohibit-password","PasswordAuthentication no","KbdInteractiveAuthentication no","PubkeyAuthentication yes","AuthorizedKeysFile "+home+"/.ssh/authorized_keys","UsePAM no","StrictModes yes","LogLevel VERBOSE"]
 r.stdin.write(b"cat > /tmp/qnx11-sshd.conf <<'SSHC'\n");r.stdin.flush();time.sleep(.1)
 for line in config:r.stdin.write((line+chr(10)).encode());r.stdin.flush();time.sleep(.04)
 r.stdin.write(b"SSHC\n");r.stdin.flush();time.sleep(.1)
 text=command(sshd+" -D -e -f /tmp/qnx11-sshd.conf > /tmp/qnx11-sshd.log 2>&1 & SSHD=$!; sleep 2; cat /tmp/qnx11-sshd.log; echo SSH_SERVER_READY","SSH_SERVER_READY");(out/"ssh-server.txt").write_text(text)
 client=["ssh","-v","-T","-i","/home/ubuntu/.openclaw/.secrets/qnx-test/id_ed25519","-o","BatchMode=yes","-o","StrictHostKeyChecking=accept-new","-o","UserKnownHostsFile=/home/ubuntu/.openclaw/.secrets/qnx-test/known_hosts","-o","ConnectTimeout=20","-o","ConnectionAttempts=1","-o","ControlMaster=no","-o","ControlPath=none","-o","ServerAliveInterval=2","-o","ServerAliveCountMax=3","-p",str(port),"root@127.0.0.1","PATH=/proc/boot:/system/bin:/bin:/usr/bin; export PATH; echo AUTH_OK; n=0; while :; do echo SSH_TICK_$n; n=$((n+1)); /proc/boot/sleep 1; done"]
 ssh=subprocess.Popen(client,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=sshlog)
 def readssh():
  for row in iter(ssh.stdout.readline,b""):
   with open(out/"ssh-stream.txt","ab") as log:log.write(row)
   if row.startswith(b"SSH_TICK_"):ticks.append({"counter":int(row.strip().split(b"_")[-1]),"host_monotonic":time.monotonic()})
 ssh_thread=threading.Thread(target=readssh,daemon=True);ssh_thread.start();deadline=time.monotonic()+30
 while not ticks and ssh.poll() is None and time.monotonic()<deadline:time.sleep(.05)
 if not ticks:raise RuntimeError("SSH authentication/stream failed: "+(out/"ssh-debug.txt").read_text(errors="replace")[-1200:])
 report["ssh"]={"client_pid":ssh.pid,"loopback_port":port,"before_counter":ticks[-1]["counter"],"single_process_single_connection":True}
 text=command("/proc/boot/slm -V -n /dev/slm-canopy -R 5/min -s canopy-can /proc/boot/slm-can-fallback.xml > /tmp/slm.log 2>&1 & sleep 3; cat /tmp/slm.log; /proc/boot/slmctl -n /dev/slm-canopy 'listall -v'; pidin ar; echo SLM_START_DONE","SLM_START_DONE")
 (out/"startup.txt").write_text(text);print(text,flush=True);current=pid(text,"dev-can-linux")
 for number in range(1,4):
  check=command("pidin ar; echo ID_CHECK","ID_CHECK");assert pid(check,"dev-can-linux")==current and pid(check,"io-sock")==mainpid and current!=mainpid
  assert ssh.poll() is None and ticks
  before=ticks[-1]["counter"]
  start=time.monotonic();text=command("kill -9 "+str(current)+"; sleep 3; /proc/boot/slmctl -n /dev/slm-canopy 'active -v'; pidin ar; ls /dev/can0/rx0; echo RESTART_DONE","RESTART_DONE")
  new=pid(text,"dev-can-linux");assert new!=current and pid(text,"io-sock")==mainpid
  assert "/dev/can0/rx0" in text and "No such file" not in text
  report["restarts"].append({"run":number,"killed_pid":current,"new_pid":new,"main_pid_unchanged":True,"observed_seconds_including_fixed_3s_settle":time.monotonic()-start});current=new;print("NATIVE_SLM_RESTART_PASS "+str(number),flush=True)
  report["restarts"][-1]["traffic"]=traffic(number)
  assert ssh.poll() is None and ticks[-1]["counter"]>before
  report["restarts"][-1]["ssh"]={"same_client_pid":ssh.pid,"counter_before":before,"counter_after":ticks[-1]["counter"]}
  print("AUTHENTICATED_SAME_SESSION_PASS "+str(number),flush=True)
 report["success"]=True
 report["ssh_authenticated_continuity"]="PASS"
 report["ssh"]["ticks"]=ticks
 command("cat /tmp/qnx11-sshd.log; echo SSH_LOG_DONE","SSH_LOG_DONE")
except Exception as error:
 try:
  diag=command("cat /tmp/qnx11-sshd.log; netstat -an; netstat -in; pidin irqs; ifconfig -a; echo SSH_FAIL_DIAG","SSH_FAIL_DIAG");(out/"failure-diag.txt").write_text(diag)
 except Exception:pass
 report["error"]=str(error);print("NATIVE_SLM_FAIL "+str(error),flush=True)
finally:
 if ssh is not None:
  ssh.terminate()
  try:ssh.wait(5)
  except subprocess.TimeoutExpired:ssh.kill();ssh.wait()
  if ssh_thread:ssh_thread.join(2)
 sshlog.close()
 r.terminate()
 try:r.wait(10)
 except subprocess.TimeoutExpired:r.kill();r.wait()
 capture.close();qpath.unlink(missing_ok=True);report["guest_stopped_reaped"]=True;(out/"receipt.json").write_text(json.dumps(report,indent=2)+chr(10));(out/"serial.txt").write_bytes(serial);print(json.dumps(report),flush=True)
sys.exit(0 if report["success"] else 1)
