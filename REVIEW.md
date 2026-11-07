# Private capability review — 7 November 2026

Scope: CANopy only, reviewed tip `61d11d1d3b316ec31f3e770c1ecbee50977d6924`. No QEMU, SDK, guest, live network/CAN runtime, deployment or demo preparation performed. No codelab exists in this repository.

**[Detailed claim-by-claim appendix](docs/review-claims.json)** covers every nonempty README/STATUS paragraph and visible block of both current site pages (including controls/labels). Each occurrence maps to exact receipt/raw-artifact paths and SHA-256, declared tested commits, and recorded binary/image hashes. `null` means absent, never inferred from the receipt-import commit. Historical evidence and failures are unchanged. Regenerate/check with `python3 tools/review_claims.py --write` / `python3 tools/review_claims.py`.

| Claim family | Label / exact evidence | Binding and gap |
|---|---|---|
| Three native libcan 100 RX/100 TX runs | **observed in this QEMU run**; `docs/acceptance/native-can-20261106/` run1–3 serial, native RX and host/expected arrays | Summary records image `1b69809c8aa7216f12c278a601fe114bed40f0cd9116e54b9988dd5c1d1f5742`; historical tested source commit / driver binary **UNVERIFIED**. Not SocketCAN. |
| SLM PID-only → post-restart traffic → authenticated SSH continuity | **observed in this QEMU run**; `docs/acceptance/slm-20261107/`, `slm-traffic-20261107/`, `slm-continuity-20261107/` receipts, serial, traffic and SSH raw logs | First two image `aae3310d80ea7190e4a03a5849d0d53770996164825cbc616eb3e22e7d1a0205`; continuity image `84fc4eda34654854333cf71320b375f2eedae405a3849475623c179443f616f1`. Source commit / driver hash **UNVERIFIED**; image hashes are recorded assertions, not rehashed external images. PID-only runs do NOT prove SSH. |
| C6 compile / runtime failure | Compile-only; runtime **UNVERIFIED**, last execution FAIL, **STOPPED**; `docs/acceptance/safestop-build-20261107/` and both failure directories | Compile receipt binds source hashes and output `dc8a5b660548e6857d11363218fd49000529b0b5de505c60f3ae7327870cdead`; no tested commit recorded. Raw final tick count 850 versus one captured heartbeat. No retry, accepted safety scenario or scheduler fix. |
| Incident viewer / corrupt, missing, mixed rejection / Chromium | **host-only**; pinned manifest, `workbench-20261107.json`, `unknown-review-20261107/`, `browser-20261107/` | Browser source `25ca8cf919e81fa62669f2cb8f813fa2cab536df`; eight recorded cases at 1280/520. **UNKNOWN** is rejection, not native acceptance. External screenshot hashes are assertions only in this repo. |
| Host model, replay controls, CRC/latch, DBC/VSS, learned pilot/C parity, doctor and SDK guard | **host-only**; exact tests/source and saved raw host logs indexed in appendix | Pinned full-suite commits in `host-review-20261107/receipt.json`; current host rerun recorded separately. Host binary hashes generally absent / **UNVERIFIED**, never promoted to native proof. Old replay/browser and live-vcan historical source bindings are **UNVERIFIED** where absent. |
| SocketCAN native ABI, QPP, QSTI provenance, full production policy, target pilot | **UNVERIFIED**; boundary docs/tests are not acceptance receipts | No matching native acceptance; no safety, timing, continuous availability, certification or production-isolation claim. |

## Corrections / interpretation

- README/STATUS now point here; historical “fresh” means fresh at the dated capture, not this review. Original sequence retained. C6’s old “one focused fix attempt next” is historical and superseded by STOPPED.
- Removed mutable “host now has vcan0 UP” and “current QEMU” language: old setup observations are not current readiness evidence.
- Current generated workbench already explicitly disclaims driver/source provenance and independent image rehash; renderer reconciliation is checked, without changing pins or historical browser inputs. Replay is permanently host-only.
- Unsupported broader readings must be removed/softened, not accepted: reproducible historical target build, installed SDK/image provenance, SSH/platform health outside the bounded stream, continuous CAN service, measured restart latency, native safety or full C3 policy.
- Tests/source are supporting implementation evidence, not a historical runtime receipt. Appendix conservatively marks absent binding **UNVERIFIED** even where a behavior currently has host regression coverage.

## This review validation

Host-only full suite: **137 total / 129 passed / 8 skipped** (three new review-coverage regressions; optional live integrations skipped). Exact-source rerun receipt and logs: `docs/acceptance/private-review-20261107/`. Offline raw CAN/SLM/SSH verification, ledger, deterministic site reconciliation, appendix and SDK guard pass; no native runtime executed.

Private editorial draft: [shot list and narration](docs/private-demo.md), planned below three minutes. No recording/upload or new runtime claim.

## Council gate and dry readiness — 17:08 UTC

Council CONDITIONAL acceptance covers scoped evidence at79912ef4ab2a738263d1ea22d42210d722182f35; native features are FROZEN. Initial offline-review statements above describe their dated revision, not a claim that later private dry preparation never happened. Current dry pack: docs/proof-capture/SCRIPT.md and report.json, exact190words/155planned seconds; no recording/audio without separate Olly OK. Historical179word draft and126/8 browser versus129/8 later host counts keep their original receipts. No repinning, native rerun, full-platform health, safety/timing/availability promotion or new unit-test-count objective. Human learning and second independent SDK remain UNVERIFIED.
