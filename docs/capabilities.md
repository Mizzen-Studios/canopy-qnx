# Capability ledger

CANopy reusable bounded QNX incident recorder and workbench

Nov8 approved bounded executable upgrades; historical rows retain their original receipts. HOST interface checks and native observations are distinct; new independent council gate pending. New native recorder capture is separate from historical SSH record; SSH continuity unsupported for new packs. Cooperative integrity is not attestation. C6/native safety STOPPED; SocketCAN UNVERIFIED; no safety/timing/availability/platform-health claims.

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
| host-regression | host | framework | PASS | Source-bound current full Python host suite:126 passed/8 skipped. Browser rendering is separately recorded; no fresh native acceptance. | [source](../docs/acceptance/browser-20261107/receipt.json) |
| incident-browser | host | browser-render | PASS | Actual Chromium desktop1280/mobile520: recorded page separately labelled; missing/corrupt/mixed UNKNOWN with no accepted timeline. No fresh native acceptance. | [source](../docs/acceptance/browser-20261107/receipt.json) |
| byo-incident-desk | host | workflow | PASS | Local bounded pack import/query/evidence/export with explicit origin and UNKNOWN rejection. Collector declarations and hashes are cooperative integrity, not attestation. | [source](../docs/incident-pack-receipts/browser.json) |
| reusable-native-recorder | native | recorded-run | PASS | New parameterized recorder captured SLM driver kill/restart and independent ordered byte-exact100RX100TX; bounded slog2 plus actual co-located death control. No SSH continuity or continuous CAN guarantee. | [source](../docs/acceptance/native-recorder-20261108/receipt.json) |
