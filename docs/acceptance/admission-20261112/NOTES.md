# Nov12 SDK768MiB admission — BLOCKED before build

Starting private tip7038c08b39457b6c9b43308ce036ee069fbb5983 matched remote. Exclusive lease acquired. No build queued, no SDK compiler/mkifs retry, no HOST native run; all earlier native and failure receipts unchanged.

Admission conservatively reserves full768MiB guest RAM, all currently charged non-guest QEMU/controller/TCG/page-cache/buffer overhead, plus64MiB safety reserve under unchanged1GiB host memory cap. Unique768MiB smaps mapping identifies RAM resident bytes; subtraction is an accounting estimate, not an irreducible RSS measurement. Page cache may be reclaimable: do not claim a larger cap is mathematically unavoidable.

Five early samples: non-guest charge153.50→203.29MiB; full-RAM projection921.50→971.29MiB. Last remaining52.71MiB is11.29MiB below64MiB reserve: admission exit73. During requested shutdown, sampled non-guest charge595.03MiB; full-RAM projection1363.03MiB (339.03MiB over cap before reserve). Observed cgroup memory.peak834.15MiB at that sample, guest RAM resident239.125MiB; all memory.events max/oom/oom_kill0 and swap.current0. Scope removed after exit, so ultimate lifetime peak is not available; these are observed samples only.

No workload started after admission failure. ACPI shutdown requested, then existing controller QMP quit used early as charged overhead kept rising; no cap changes or guest repair. Guest/owner exit0 collected; no actual QEMU process, lease FREE, no runnable queue scripts.

## Exact commands and outcomes
- `CAN_SDK_MEMORY_MIB=768 bash .openclaw/tmp/can-features-sdk-owner.sh` → owner0, guest0.
- `python3 .openclaw/tmp/can-admission.py > /home/ubuntu/qnx-host/guest/shared/features-can-20261112/admission.log 2>&1` →73. Monitor source and exact measurement JSON alongside.
- `python3 /home/ubuntu/qnx-host/guest/guestctl-capped.py stop` →0 after QMP/ACPI success then stopped.
- Early final quit: `python3 -c "import runpy,sys; sys.argv=['guestctl-capped.py','status']; n=runpy.run_path('/home/ubuntu/qnx-host/guest/guestctl-capped.py'); print(n['request']('quit'))"` →0, status running then quit success.
- Owner EXIT cleanup repeated stop after QEMU removal: FileNotFoundError missing qmp.sock, ignored by existing trap; owner0.
- `flock -n /home/ubuntu/qnx-host/native-test.lock -c "echo LEASE_FREE"` →0; actual-process census no qemu-system.

Original controller backed up before changes (external path and hashes in receipt). Opt-in SDK memory override restricted512/768, default512 preserved; MemorySwapMax=0 tightened to exclude existing host swap. Native collector guest cap remains512MiB. CPU100%, MemoryMax1GiB, nice15,1vCPU unchanged. No guest swap configured, no host swap used. Controller patch retained for audit/reproducibility; no other system config changed.

New guest query remains qcc ELF build PASS from Nov10 only, native NOT_RUN; new same-pack adapter/desk host-only, SSH UNVERIFIED. No F dry-script refresh since native gates absent. C6 STOPPED; no SDK install/login, platform repair, single-host, public action, media or spend. Stop entire wave pending owner/parent decision; no EDU handoff implied.
