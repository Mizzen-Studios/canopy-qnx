from pathlib import Path
import os,json,time
base=Path('/home/ubuntu/qnx-host/guest/shared/features-can-20261112')
p=int(Path('/home/ubuntu/qnx-host/guest/qemu.pid').read_text())
cg=Path('/sys/fs/cgroup')/next(l.split(':',2)[2] for l in Path(f'/proc/{p}/cgroup').read_text().splitlines() if l.startswith('0::')).lstrip('/')
def sample():
 blocks=[]; b={}
 for l in Path(f'/proc/{p}/smaps').read_text().splitlines():
  words=l.split()
  if words and '-' in words[0] and ':' not in words[0]:
   if b: blocks.append(b)
   b={'map':l}
  elif len(words)>1 and words[0] in ('Size:','Rss:'): b[words[0][:-1]]=int(words[1])*1024
 if b:blocks.append(b)
 ram=[b for b in blocks if b.get('Size')==768*1024*1024]
 assert len(ram)==1,('RAM mapping ambiguous',ram)
 current=int((cg/'memory.current').read_text()); resident=ram[0]['Rss']; overhead=max(0,current-resident)
 return {'time':time.time(),'pid':p,'cgroup':str(cg),'memory_current':current,'memory_peak':int((cg/'memory.peak').read_text()),'swap_current':int((cg/'memory.swap.current').read_text()),'guest_reserved_bytes':768*1024*1024,'guest_resident_bytes':resident,'measured_total_non_guest_overhead_bytes':overhead,'full_reservation_projection_bytes':768*1024*1024+overhead,'remaining_after_full_reservation_bytes':1024*1024*1024-768*1024*1024-overhead,'memory_events':(cg/'memory.events').read_text(),'memory_stat':(cg/'memory.stat').read_text(),'ram_mapping':ram[0]}
assert (cg/'cpu.max').read_text().strip()=='100000 100000'
assert (cg/'memory.max').read_text().strip()=='1073741824'
assert (cg/'memory.swap.max').read_text().strip()=='0'
assert os.getpriority(os.PRIO_PROCESS,p)==15
rows=[]
for i in range(5):
 r=sample();rows.append(r);time.sleep(2)
reserve=64*1024*1024
admit=all(r['remaining_after_full_reservation_bytes']>=reserve and r['swap_current']==0 for r in rows)
out={'admitted':admit,'reserve_bytes':reserve,'policy':'Full768MiB guest RAM plus measured cgroup non-guest overhead (includes TCG, buffers, pagecache), plus64MiB reserve must fit1GiB. No host/guest swap. Ongoing monitor detects growth; not a future peak guarantee.','samples':rows}
(base/'admission.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
raise SystemExit(0 if admit else 73)
