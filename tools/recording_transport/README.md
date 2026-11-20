# Shared shell transport (HOST-tested, no capture authority)

Canonical portable helper for additive CAN tooling; HostShare vendors the exact
source with an immutable commit/SHA256 pin and local equality test. EDU may adopt
the same pinned release later; it is NOT integrated here. Frozen CAN product,
SDK/images, native C and historical evidence are unchanged.

64-byte octal chunks, <=512-byte physical commands, validated short destinations,
fresh128-bit nonce plus sequence/offset standalone acknowledgments. CSI is stripped
ONLY from the acknowledgment matching view; raw sends/receives remain unchanged.
Command echoes, stale/wrong/duplicate acknowledgments fail closed. No retransmit.
Final existing guest toybox sha256sum AND wc -c must match host payload BEFORE
caller chmod/exec. Missing applet, corruption or timeout aborts, never installs.
Caller must additionally honor bounded partial-write/read deadlines and append
private raw receive logs even on failure; helper emits send/reply/terminal events.
No transferred payload is ever executed by this helper.

Default transfer budget900s total; per-request <=20s clipped to remaining budget.
This replaces neither any capture deadline nor boot/conformance stage budgets.
No native acceptance/performance claim follows from these HOST tests.

Run python3 -m unittest discover -s tests/recording_transport -v.
Shared19 regressions plus4 compatibility tests cover actual HOST PTY/shell
transfer of51528 synthetic bytes (same SIZE as reviewed HS ELF),806 data chunks,
808 total acknowledgments, <=371-byte commands for the HOST destination, deliberate
2ms ack delays and fragmented7-byte writes. A separate virtual-clock model of
1s per acknowledgment finishes808s under900s; this is NOT measured QNX latency.
Actual nonblocking-pipe backpressure is separately exercised. Negative controls
include missing hash, corruption, size/hash mismatch, truncation, replay/echo,
CSI framing, invalid bounds, zero writes and global-deadline exhaustion.
