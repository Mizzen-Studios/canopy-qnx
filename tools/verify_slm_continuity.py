#!/usr/bin/env python3
"""Recheck saved native libcan/SSH evidence; never a fresh run or SocketCAN gate."""
import json
from pathlib import Path
import re
import sys
from verify_slm_traffic_evidence import verify as traffic_verify

def verify(folder):
    root=Path(folder); receipt=traffic_verify(root)
    if receipt.get('ssh_authenticated_continuity') != 'PASS': raise ValueError('SSH not accepted')
    client=receipt['ssh']['client_pid'];ticks=receipt['ssh']['ticks']
    if receipt['ssh'].get('single_process_single_connection') is not True: raise ValueError('single connection absent')
    if len(ticks)<4 or [t['counter'] for t in ticks] != list(range(len(ticks))): raise ValueError('SSH counter reset/gap')
    if any(b['host_monotonic']<=a['host_monotonic'] for a,b in zip(ticks,ticks[1:])): raise ValueError('invalid observation times')
    raw=(root/'ssh-stream.txt').read_text().splitlines()
    if raw.count('AUTH_OK') != 1 or [int(s[9:]) for s in raw if s.startswith('SSH_TICK_')] != [t['counter'] for t in ticks]: raise ValueError('stream/receipt mismatch')
    debug=(root/'ssh-debug.txt').read_text()
    if len(re.findall(r'Authenticated to .* using "publickey"',debug)) != 1: raise ValueError('actual publickey authentication missing/ambiguous')
    if 'not responding' in debug or 'timed out' in debug: raise ValueError('SSH timeout observed')
    if 'Accepted publickey for root' not in (root/'serial.txt').read_text(): raise ValueError('server authentication missing')
    previous=-1
    for row in receipt['restarts']:
        ssh=row['ssh'];before=ssh['counter_before'];after=ssh['counter_after']
        if ssh['same_client_pid']!=client or not previous<=before<after<len(ticks): raise ValueError('session changed or no postkill stream')
        previous=after
    return dict(scope='offline saved native libcan/SSH evidence only; not SocketCAN or full production policy',restarts=3,ssh_client_pid=client,ssh_ticks=len(ticks),observed_max_tick_gap_seconds=max(b['host_monotonic']-a['host_monotonic'] for a,b in zip(ticks,ticks[1:])))

if __name__=='__main__': print(json.dumps(verify(sys.argv[1]),indent=2))
