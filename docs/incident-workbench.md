# Recorded incident workbench — private review slice

Open [local read-only viewer](workbench/index.html). No server, guest or live
connection is started. Run from repository root before viewing:


default command: python3 tools/incident_workbench.py

verification only: python3 tools/incident_workbench.py --verify-only

The generator pins one exact saved experiment via
[manifest](workbench/recorded-manifest.json), then rechecks caps, PID chain,
serial phases, traffic arrays and one authenticated SSH stream. Missing,
corrupt, truncated, extra or mixed files and modified/repinned manifest yield
UNKNOWN, status2; generated UNKNOWN pages have no PASS panel. No import is
silently promoted to the known run. Tests mutate copies, never saved evidence.

## Read the journey

1. Observed CAN PID identified before kill.
2. Kill and fixed3-second settle, then different CAN PID/device snapshot.
3. Ordered byte-exact100RX +100TX against independent host arrays.
4. Later counters on the same authenticated SSH connection; main io-sock PID
   unchanged in snapshots. Three repetitions are recorded.

This is causal phase order, not clock alignment. Host monotonic SSH seconds
and native serial CAN timestamps remain separate. Windows include settle;
there is no continuous-availability or exact recovery-latency claim.

**observed in this QEMU run · app budget, not a QNX benchmark**.

## Permanent limits

- Static HTML is an at-generation snapshot, not live integrity attestation.
  Re-run the verifier after any evidence change. It detects file mixing, not
  an adversary able to replace verifier source and its pins.
- Exact saved controller is linked and hashed. Current helper hashes identify
  this offline review only. Historical driver source/build identity remains
  UNPROVEN; receipt image hash is not independently rehashed without the image.
- [Host simulation](replay/index.html) is a different evidence journey forever.
- C6 FAIL / STOPPED; SocketCAN BLOCKED / UNVERIFIED. No heartbeat work restarted.
- No physical safety, certification, production isolation, continuous CAN
  availability, latency or QNX benchmark claim. Nothing published/deployed.

The canonical [capability ledger](capabilities.md) is the declaration source.

## UNKNOWN recovery and disposable review copies

UNKNOWN now explains a bounded recovery: preserve the failing copy/error; never repin to silence it; restore the complete matching capture into a separate clean checkout; run the offline verifier. If exact matching evidence is unavailable, retain UNKNOWN. Only a verified recording can be regenerated; no guest is started and C6 is not repaired. Static PASS is generation-time only.

Generate private review fixtures with `python3 tools/unknown_review_fixtures.py`. It mutates only temporary capture copies, then saves [missing](acceptance/unknown-review-20261107/missing.html), [corrupt](acceptance/unknown-review-20261107/corrupt.html) and [mixed](acceptance/unknown-review-20261107/mixed.html) UNKNOWN HTML outside docs/workbench/index.html. The [receipt](acceptance/unknown-review-20261107/receipt.json) records each command, input mutation, outcome and page digest. These deliberately rejected host fixtures are not native runs or authoritative PASS artifacts. No deployment. Subsequent [actual local Chromium validation](acceptance/browser-20261107/NOTES.md) covers these saved pages; not human review or fresh native acceptance.
