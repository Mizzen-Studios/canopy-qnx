#!/usr/bin/env python3
"""Private libcan fallback acceptance, NOT an io-sock/SocketCAN target gate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import socket
import struct
import subprocess
import time

QUALIFIER = "observed in this QEMU run · app budget, not a QNX benchmark"

def parse_qnx(text):
    rows = []
    pattern = re.compile(r"^\s*/dev/can0/rx0 TS: \d+ms \[SFF\] ([0-9a-fA-F]+) \[8\] ((?:[0-9a-fA-F]{2} ){7}[0-9a-fA-F]{2})\s*$")
    for line in text.splitlines():
        if '/dev/can0/rx0' not in line:
            continue
        match = pattern.fullmatch(line)
        if not match:
            raise ValueError('malformed QNX frame: ' + line)
        rows.append((int(match[1], 16), match[2].replace(' ', '').lower()))
    return rows

def require_exact(expected, actual):
    if len(expected) != 100 or len(actual) != 100 or expected != actual:
        raise ValueError(f'count/order/bytes mismatch: expected={len(expected)} actual={len(actual)}')
    if len({x[0] for x in actual}) != 100 or len({x[1] for x in actual}) != 100:
        raise ValueError('IDs and payloads must each vary across all 100 frames')

def assert_caps():
    path = next(line.split(':', 2)[2] for line in Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0:'))
    cg = Path('/sys/fs/cgroup') / path.lstrip('/')
    cpu = (cg / 'cpu.max').read_text().strip()
    mem = (cg / 'memory.max').read_text().strip()
    quota, period = cpu.split()
    if quota == 'max' or int(quota) > int(period) or mem == 'max' or int(mem) > 1073741824 or os.getpriority(os.PRIO_PROCESS, 0) < 15:
        raise RuntimeError('refusing missing native cgroup/nice caps')
    return {'cpu.max': cpu, 'memory.max': mem, 'nice': os.getpriority(os.PRIO_PROCESS, 0)}

def run_once(image, output, number):
    base = output / f'run{number}'
    qpath = output / f'qt{number}.sock'
    mpath = output / f'qm{number}.sock'
    for path in (qpath, mpath):
        if path.exists():
            raise RuntimeError('socket exists; inspect owner before retry')
    args = ['qemu-system-x86_64', '-machine', 'pc,accel=tcg', '-cpu', 'max',
            '-smp', '1', '-m', '512', '-display', 'none', '-serial', 'stdio',
            '-monitor', 'none', '-no-reboot', '-kernel', str(image/'ifs-edu-resmgr.bin'),
            '-drive', f'file={image}/disk-edu-libc,format=raw,if=ide,snapshot=on',
            '-nic', 'user,model=virtio-net-pci', '-object', 'can-bus,id=canbus0',
            '-device', 'kvaser_pci,canbus=canbus0', '-device', 'edu,dma_mask=0xffffffff',
            '-object', 'can-host-socketcan,id=hostcan0,if=vcan1,canbus=canbus0',
            '-qtest', f'unix:{qpath},server=on,wait=off',
            '-qmp', f'unix:{mpath},server=on,wait=off']
    capture = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
    capture.bind(('vcan1',))
    capture.setblocking(False)
    frames = []
    serial = bytearray()
    r = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    sel = selectors.DefaultSelector()
    sel.register(r.stdout, selectors.EVENT_READ)
    def drain():
        while True:
            try:
                raw = capture.recv(16)
            except BlockingIOError:
                break
            cid, dlc, payload = struct.unpack('=IB3x8s', raw)
            frames.append((cid, payload[:dlc].hex()))
    def until(marker, timeout=100):
        start = len(serial)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            drain()
            if sel.select(.02):
                data = os.read(r.stdout.fileno(), 65536)
                if not data:
                    raise RuntimeError('QEMU exited before marker')
                serial.extend(data)
            if marker in bytes(serial[start:]).replace(b'\r', b'').split(b'\n'):
                return bytes(serial[start:]).decode(errors='strict')
            if r.poll() is not None:
                raise RuntimeError('QEMU died')
        raise TimeoutError(marker)
    def command(line):
        r.stdin.write((line+'\n').encode())
        r.stdin.flush()
    route = []
    try:
        until(b'QNX_RX_READY')
        q = socket.socket(socket.AF_UNIX)
        q.settimeout(3)
        q.connect(str(qpath))
        f = q.makefile('rwb', buffering=0)
        def qt(cmd):
            f.write((cmd+'\n').encode())
            response = f.readline().decode().strip()
            route.append([cmd, response])
            if not response.startswith('OK'):
                raise RuntimeError('qtest command failed')
            return response
        qt('outl 0xcf8 0x80000860')
        qt('inl 0xcfc')
        qt('outl 0xcfc 0x0a0a0a0a')
        if int(qt('inl 0xcfc').split()[-1], 16) != 0x0a0a0a0a:
            raise RuntimeError('PIRQ override readback mismatch')
        f.close()
        q.close()
        until(b'QNX_EDU_GATE_END')
        command('/proc/boot/cansend -h > /tmp/c2-help; cat /tmp/c2-help; echo C2_HELP_DONE')
        helptext = until(b'C2_HELP_DONE')
        if '-m subopts' not in helptext or 'Standard (0)' not in helptext:
            raise RuntimeError('unexpected libcan cansend CLI')
        command('/proc/boot/candump -u0,rx0 > /tmp/c2-rx 2>&1 & C2_RX=$!; sleep 1; echo C2_READY')
        until(b'C2_READY')
        time.sleep(.3)
        drain()
        frames.clear()
        cmd = ['cangen', 'vcan1', '-n', '100', '-I', 'i', '-L', '8', '-D', 'i', '-g', '30']
        gen = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        end = time.monotonic()+10
        while gen.poll() is None and time.monotonic()<end:
            drain()
            time.sleep(.01)
        if gen.poll() is None:
            gen.kill(); gen.wait()
            raise TimeoutError('cangen')
        out, err = gen.communicate()
        if gen.returncode:
            raise RuntimeError(err.decode())
        time.sleep(.3)
        drain()
        host_rx = list(frames)
        command('kill -INT $C2_RX; wait $C2_RX; echo C2_RX_BEGIN; cat /tmp/c2-rx; echo C2_RX_END')
        rx_text = until(b'C2_RX_END')
        qnx_rx = parse_qnx(rx_text)
        base.with_suffix('.rx-qnx.txt').write_text(rx_text)
        base.with_suffix('.rx-host.json').write_text(json.dumps(host_rx, indent=2)+'\n')
        require_exact(host_rx, qnx_rx)
        expected = [(0x400+i, bytes((i*17+j*29+number) % 256 for j in range(8)).hex()) for i in range(100)]
        frames.clear()
        command("cat > /tmp/c2-tx.sh <<'C2_SCRIPT'")
        for cid, payload in expected:
            command(f'/proc/boot/cansend -u0,tx0 -m0x{cid:x},0,0x{payload} || exit 1')
            command('sleep 0.03')
        command('C2_SCRIPT')
        command('sh /tmp/c2-tx.sh; C2_RC=$?; echo C2_TX_RC=$C2_RC; echo C2_TX_END')
        tx_text = until(b'C2_TX_END', timeout=60)
        time.sleep(.3)
        drain()
        base.with_suffix('.tx-host.json').write_text(json.dumps(frames, indent=2)+'\n')
        base.with_suffix('.tx-expected.json').write_text(json.dumps(expected, indent=2)+'\n')
        if 'C2_TX_RC=0' not in tx_text.replace('\r','').splitlines():
            raise RuntimeError('native cansend script failed')
        require_exact(expected, frames)
        result = {'run': number, 'pass': True, 'hostCangenCommand':cmd,
                  'rxHostCount':len(host_rx), 'rxQnxCount':len(qnx_rx),
                  'txExpectedCount':len(expected), 'txHostCount':len(frames),
                  'orderedByteExact':True, 'nativeAPI':'libcan /dev/can0, NOT SocketCAN',
                  'qualifier':QUALIFIER, 'routingOverride':route, 'settleSeconds':.3}
        base.with_suffix('.result.json').write_text(json.dumps(result, indent=2)+'\n')
        return result
    finally:
        r.terminate()
        try:
            r.wait(10)
        except subprocess.TimeoutExpired:
            r.kill(); r.wait(10)
        base.with_suffix('.serial.txt').write_bytes(serial)
        base.with_suffix('.routing.json').write_text(json.dumps(route, indent=2)+'\n')
        capture.close()
        sel.close()
        for path in (qpath, mpath):
            path.unlink(missing_ok=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image_dir', type=Path)
    parser.add_argument('output_dir', type=Path)
    a=parser.parse_args()
    caps=assert_caps()
    a.output_dir.mkdir(parents=True, exist_ok=False)
    meta={'qualifier':QUALIFIER, 'caps':caps, 'runs':[], 'pass':False,
          'sourceGate':'libcan fallback acceptance ONLY; io-sock C2 NOT passed',
          'imageSha256':hashlib.sha256((a.image_dir/'ifs-edu-resmgr.bin').read_bytes()).hexdigest(),
          'qemuVersion':subprocess.check_output(['qemu-system-x86_64','--version'],text=True).splitlines()[0]}
    try:
        for number in range(1,4):
            meta['runs'].append(run_once(a.image_dir, a.output_dir, number))
            print(json.dumps(meta['runs'][-1]), flush=True)
        meta['pass']=len(meta['runs'])==3
    except Exception as e:
        meta['error']=str(e)
        raise
    finally:
        (a.output_dir/'summary.json').write_text(json.dumps(meta,indent=2)+'\n')
    return 0 if meta['pass'] else 1

if __name__=='__main__':
    raise SystemExit(main())
