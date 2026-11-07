import sys,os,time,json,re,subprocess,selectors,hashlib,fcntl
from pathlib import Path
sys.path.insert(0,"/home/ubuntu/.openclaw/workspace/apps/canopy-qnx/tools")
from native_can_three import assert_caps
out=Path("/home/ubuntu/.openclaw/workspace/.openclaw/tmp/qnx-followup10/slm-parent");out.mkdir(exist_ok=True)
lock=open("/home/ubuntu/qnx-host/native-test.lock","w");fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
caps=assert_caps();image=Path("/home/ubuntu/qnx-host/guest/shared/qnx-native/ifs-slm-followup10.bin")
assert hashlib.sha256(image.read_bytes()).hexdigest()=="aae3310d80ea7190e4a03a5849d0d53770996164825cbc616eb3e22e7d1a0205"
args=["qemu-system-x86_64","-machine","pc,accel=tcg","-cpu","max","-smp","1","-m","512","-display","none","-serial","stdio","-monitor","none","-no-reboot","-kernel",str(image),"-drive","file=/home/ubuntu/qnx-host/guest/shared/qnx-native/disk-edu-libc,format=raw,if=ide,snapshot=on","-nic","user,model=virtio-net-pci","-object","can-bus,id=canbus0","-device","kvaser_pci,canbus=canbus0","-device","edu,dma_mask=0xffffffff"]
r=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);sel=selectors.DefaultSelector();sel.register(r.stdout,selectors.EVENT_READ);serial=bytearray();report={"caps":caps,"qemu_pid":r.pid,"image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),"label":"observed in this QEMU run; app budget, not QNX benchmark","restarts":[],"success":False,"ssh_authenticated_continuity":"UNVERIFIED"}
def until(marker,timeout=60):
 start=len(serial);end=time.monotonic()+timeout
 while time.monotonic()<end:
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
try:
 until("CANOPY_SLM_IMAGE_READY",100)
 baseline=command("pidin ar; echo BASE_DONE","BASE_DONE");mainpid=pid(baseline,"io-sock");report["main_io_sock_pid"]=mainpid
 text=command("/proc/boot/slm -V -n /dev/slm-canopy -R 5/min -s canopy-can /proc/boot/slm-can-fallback.xml > /tmp/slm.log 2>&1 & sleep 3; cat /tmp/slm.log; /proc/boot/slmctl -n /dev/slm-canopy 'listall -v'; pidin ar; echo SLM_START_DONE","SLM_START_DONE")
 (out/"startup.txt").write_text(text);print(text,flush=True);current=pid(text,"dev-can-linux")
 for number in range(1,4):
  check=command("pidin ar; echo ID_CHECK","ID_CHECK");assert pid(check,"dev-can-linux")==current and pid(check,"io-sock")==mainpid and current!=mainpid
  start=time.monotonic();text=command("kill -9 "+str(current)+"; sleep 3; /proc/boot/slmctl -n /dev/slm-canopy 'active -v'; pidin ar; ls /dev/can0/rx0; echo RESTART_DONE","RESTART_DONE")
  new=pid(text,"dev-can-linux");assert new!=current and pid(text,"io-sock")==mainpid
  assert "/dev/can0/rx0" in text and "No such file" not in text
  report["restarts"].append({"run":number,"killed_pid":current,"new_pid":new,"main_pid_unchanged":True,"observed_seconds_including_fixed_3s_settle":time.monotonic()-start});current=new;print("NATIVE_SLM_RESTART_PASS "+str(number),flush=True)
 report["success"]=True
except Exception as error:
 report["error"]=str(error);print("NATIVE_SLM_FAIL "+str(error),flush=True)
finally:
 r.terminate()
 try:r.wait(10)
 except subprocess.TimeoutExpired:r.kill();r.wait()
 report["guest_stopped_reaped"]=True;(out/"receipt.json").write_text(json.dumps(report,indent=2)+chr(10));(out/"serial.txt").write_bytes(serial);print(json.dumps(report),flush=True)
sys.exit(0 if report["success"] else 1)
