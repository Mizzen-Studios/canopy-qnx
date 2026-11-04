#!/bin/bash
set -euo pipefail
uname -m
dpkg --print-architecture
getconf GNU_LIBC_VERSION
gcc --version | head -1
python3 - <<'PY'
import subprocess,time,concurrent.futures,json
start=time.monotonic();subprocess.run(["gcc","-Wall","-Wextra","-Werror","-pthread","/smoke/smoke.c","-ldl","-o","/tmp/smoke"],check=True);compile_s=time.monotonic()-start
start=time.monotonic();subprocess.run(["/tmp/smoke"],check=True);runtime_s=time.monotonic()-start
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    values=list(executor.map(lambda x:subprocess.check_output(["/bin/echo",str(x)],text=True).strip(),range(4)))
assert values==["0","1","2","3"]
print(json.dumps({"compile_s":compile_s,"runtime_s":runtime_s,"threaded_python_subprocesses":len(values),"label":"observed on this VM; Linux compiler smoke, NOT QNX/qcc"}))
PY
file /tmp/smoke
readelf -l /tmp/smoke | grep interpreter
