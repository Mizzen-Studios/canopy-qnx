# CANopy — one fresh live recording,15 November2026

**PASS, scoped original build only.** One native run, no retry. Original Nov8 recorder/image was executed freshly, with new run/raw/traffic/disk bindings. No claim that the later guest-query feature ran. Historic receipts are unchanged.

- SLM driver278546 killed by recorder315408, replacement331794 observed; io-sock163853 appears before/after.
- Independent host byte oracle: ordered100RX and100TX, IDs and every payload byte exact.
- Finite5slog2 event sequence and co-located co-failure control in same serial capture.
- Actual HOST browser imported this new pack, answered four bounded questions, then rejected a corrupt digest as UNKNOWN with queries disabled. No QNX web-server claim.
- SSH UNVERIFIED. No safety, latency or continuous-availability claim. Settle time includes fixed3s wait and is not a latency figure.

## Capture
`systemd-run --user --scope -p CPUQuota=100% -p MemoryMax=2G -p MemorySwapMax=0 nice -n15 python3 .openclaw/tmp/can-recording-20261115/capture-live.py --image /home/ubuntu/qnx-host/guest/shared/incident-20261108/incident.ifs --disk /home/ubuntu/qnx-host/guest/shared/qnx-native/disk-edu-libc --out /home/ubuntu/.openclaw/workspace/.openclaw/tmp/can-recording-20261115/live --lock /home/ubuntu/qnx-host/native-test.lock --interface vcan1` → exit0.

Capture-only helper is outside repository, derivative of pre-query collector7c711db (original hash99e8b785fa85e20cfd7650e2e869c401bf14bca3997a1bf470c4fa7a3ad1ccaf). It records actual serial chunks and command events before execution, adds resource sampling/TCG256, and omits unrelated ability commands. No project source or features changed; no SDK build/login. Host vcan is only transport, not proof of target SocketCAN. Existing libcan PIRQ routing adjustment retained and recorded; no C6/controller/heartbeat code path executed.

HOST caps100%CPU/2GiB/nice15/swap0; guest512MiB/1vCPU/TCG256. Observed cgroup peak639528960bytes;64MiB reserve comfortably retained; zero memory max/oom/kill events. Guest exited0 and was reaped immediately after native run; lease FREE before host browser/render.

## Video and private review
Final MP4 and still paths/hashes are in recording.json;150s,1920x1080,H26425fps, silent/no audio, full decode PASS. Captions disclose selected output, omitted waits and readable holds. No old footage, synthetic terminal verdicts or personal paths displayed. Actual raw event reconstruction is byte-checked; row offsets/timestamps and actual browser frame mappings are in video-provenance.json. Browser screenshot timestamps use recorded file-time alignment normalized to first frame; not a benchmark clock.

Intermediate host-only edit attempts (including an early boundary spilling UNKNOWN into the last VALID chapter frame) remain outside git; reviewed final corrects that boundary solely from the same captured frames. No target/browser run was repeated for the edit.

Only receipts/logs committed. No SDK bytes or large media in git. Private draft release upload only; nothing public, no spend. Stop for review; no further runs or features scheduled.
