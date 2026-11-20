# Recording attempt failure record — 20 November 2026

**FAILED / STOPPED. No successful item5 recording or new accepted incident pack.**

The frozen product remains at source commit `4c9413e87095894c3a4567782ecf60c4afaf1794`. This documentation-only milestone does not change that freeze. No SDK build/install, C6 execution, guest-query acceptance, SSH/SocketCAN verification, private Nov15d pack access, upload or publication occurred.

## Attempts and original statuses

1. 19 November: QEMU rejected an AF_UNIX qtest pathname exceeding107 bytes before QNX boot. Original receipt remains success=false,error=guest died. Short private socket admission was subsequently tested HOST ONLY:59-byte derived paths, actual bind/connect for each reserved role, kernel107-byte positive and108-byte negative boundary. This fix did not repair or reseal the failed receipt.
2. Fresh owner-authorized20November run `native-6e183d5398ea4df8a85b258ce4426b2a`: QNX booted, SLM replacement278546→331794 observed, main io-sock163853 unchanged in process snapshots. The finite TX journey failed waiting for TX_DONE. Original receipt remains success=false,error=TX_DONE,guest_stopped_reaped=true. No completed traffic1 result, no100/100 new TX claim, no fresh pack/comparison/browser success or finished demonstration video.

Both original receipt hashes and sanitized source/input bindings are in [receipt.json](receipt.json). Raw serial, licensed inputs and failure footage remain private outside Git. The latter is actual continuous H26425fps silent footage126.24s, not a deliverable or a successful demonstration.

## Host-only diagnosis from retained bytes

Proven observations:
- Generated send records are77 bytes including two newlines; nominal per-record drain/send pacing is0.1s. The sender does not await an echoed line or receiver acknowledgment and does not read back/hash the completed guest file before execution.
- Reassembled received transfer serial is6830 bytes over4779 timestamped chunks. Per-event chunk boundaries are not terminal-line boundaries; analysis concatenates bytes before CR-normalization/line splitting.
-71 complete expected send-command echo lines and72 complete sleep-command echo lines were retained. Around identifier0x448, multiple command prefixes and payload fragments merge into one617-byte echo line. The closing C3_SCRIPT delimiter appears appended to that malformed line rather than as an independent delimiter. No standalone TX_DONE line was observed.
- The shell remains at its continuation prompt after the host sends the execution command. That is consistent with an unterminated here-document; original90s marker wait expires. This is not evidence of observed CAN-frame loss or of a CAN driver defect.

Bounded inference: the retained stream demonstrates a transfer/framing failure visible at the guest console, not its precise layer. UART/input queue loss, terminal/shell editing and host/QEMU serial flow-control behavior remain hypotheses. The tap proves received bytes, not every host write's exact delivery. No guest termios/queue-limit snapshot, exact write-boundary log or completed-file checksum exists. A generic Linux PTY limit cannot establish the QNX limit.77-byte generated records alone do not establish a per-line limit violation.

## Cleanup and resource bounds

Own QEMU1112198 terminated/reaped by08:24:23UTC; subsequent anchored host process scan empty and canonical lease probe succeeded. Supervisor returncode1,breach=null,peak518316032 bytes,reserve67108864 bytes,own_tree_reaped=true. Its status COMPLETE means supervisor completion, **not incident success**. Native1GiB, aggregate2GiB, swap0, CPU100%,nice15,guest512MiB,smp1,TCG256 were enforced. No resource breach or automatic second attempt. Process snapshots are not continuous availability evidence; QEMU demo is not a safety/latency claim.

## Proposed next preparation, not permission to execute

Keep the current failed originals unchanged. Before any separately authorized native attempt: log exact host write spans/timestamps and received byte spans; use acknowledged small chunks with bounded timeout/backpressure instead of a fixed-rate unacknowledged here-document; confirm a standalone closing delimiter and verify guest file length/hash before execution. Abort and reap on any mismatch; do not retry automatically or raise caps. Test the transport state machine HOST ONLY with injected truncation/delimiter loss/backpressure first. Any future transfer must remain wholly omitted from visible footage using actual measured boundaries, with original raw bytes retained privately. Fresh owner authority is required for another guest.
