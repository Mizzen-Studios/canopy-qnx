# Single authorized low-memory CANopy retry — BLOCKED

Existing failure `../query-20261110/` remains unchanged. Retry source `2879bf8848daffca66fabb4a6a7d5e96d2141a5a`, clean tracked archive.

## Precise diagnosis
All three qcc ELF compile/link stages returned0. Failure is inside mkifs: its qcc-driven x86_64-pc-nto-qnx8.0.0-ld process1075 relinking existing procnto-smp-instr to procnto-smp-instr.sym with --no-keep-memory. Kernel OOM killed it at guest567.044006s: total-vm588920kB, anon-rss332584kB, file-rss1732kB. IFS remains empty. This is not a guest_query.c compilation failure. Prior libexpat warning remains separate, not asserted causal.

Before mkifs: available327000KiB;14 process/free samples, minimum sampled available21948KiB, maximum sampled linker RSS319384KiB (kernel kill data is later). Memory samples include full exact linker argv, top resident process census and free output. No swap configured or activated.

## Low-memory tactics and commands
- Existing licensed SDK only. Waited for cloud-init boot-finished before build, then narrowly inspected active allowlisted units. Temporarily stopped active snapd.socket, apport.service, udisks2.service; others were inactive. No service disabled/masked/config edited. Queue/session bus untouched.
- Strict serial qcc ELF builds followed by separate mkifs stage; MAKEFLAGS preserves SDK include flags plus -j1. No extra optimization/debug flags added.
- Exact launcher `launch.sh`; source build script at bound SHA. Existing controller command: `python3 /home/ubuntu/qnx-host/guest/guestctl-capped.py exec /home/ubuntu/qnx-host/guest/shared/features-can-retry-20261110/launch.sh 1500`; job1794305218237972855.
- Queue never emitted .rc after OOM/termination; no fabricated mkifs exit code. Waiting host client SIGTERM-cancelled after observed blocker. Build log records termination, not a completed IFS.
- Launcher includes best-effort service restoration trap, but no RESTORED_UNITS confirmation was produced after OOM. No permanent service changes; guest powered off. Do not claim observed restoration.
- `python3 /home/ubuntu/qnx-host/guest/guestctl-capped.py stop` invoked once; owner cleanup/lease verification recorded in receipt.

No HOST native QNX run: A native query, B recorder/SSH and C same-pack native desk acceptance NOT_RUN; SSH UNVERIFIED. F withheld pending parent decision. Historical native evidence unchanged. No retry beyond this single attempt, no platform repair, packages, swap, cap increase, license/login, C6, media, publication or spend.

Build log SDK export banner removed; unmodified original remains external. Serial is this boot segment from append-only host log. Licensed binaries/IFS are not committed; artifact hashes preserve empty IFS explicitly.
