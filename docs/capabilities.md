# Capability ledger

CANopy fault-containment incident workbench

Recorded native libcan + SLM experiment, not native vehicle safety. C6 FAIL/stopped; no automatic retries or new heartbeat work. SocketCAN blocked. No continuous CAN availability, physical-safety, certification, latency or QNX benchmark claim.

Canonical declarations: docs/capabilities.json. Generated view; ledger checks are not runtime acceptance.

**Native observations: observed in this QEMU run · app budget, not a QNX benchmark.**

| Capability | Domain | Level | Status | Bounded claim | Evidence |
|---|---|---|---|---|---|
| host-model | host | simulation | PASS | Host deterministic simulation and Linux vcan only; never QNX | [source](../docs/host-runtime.md) |
| native-libcan | native | reference-run | PASS | Three ordered byte-exact100RX/100TX runs; libcan fallback, not SocketCAN | [source](../docs/acceptance/native-can-20261106/summary.json) |
| slm-ssh | native | recorded-run | PASS | Three exact CAN PID kills/restarts, post-restart100RX/100TX exact, same authenticated SSH connection; causal phases only | [source](../docs/acceptance/slm-continuity-20261107/receipt.json) |
| socketcan | native | runtime | UNVERIFIED | Blocked matching x86_64 module/board ABI; not an accepted C2/C3 stack | [source](../docs/socketcan-demo.md) |
| c6 | native | runtime | FAIL | STOPPED:850 native TX attempts versus1 host heartbeat; root cause undetermined, no accepted functional scenarios | [source](../docs/acceptance/safestop-focused-failure-20261107/receipt.json) |
| incident-viewer | host | recorded-evidence-view | PASS | Local read-only generation-time view of pinned recorded QNX evidence; missing/corrupt/mixed/repinned evidence UNKNOWN; historical driver identity UNPROVEN | [source](../docs/acceptance/workbench-20261107.json) |
