# Immutable historical analysis — 19 November 2026

Item 1 only. Baseline main/origin 50e5751090108d8ffc5e963382882fb0656f815a. Parent independent verification required before item 2.

API mode `historical`, CLI `--historical`, and explicit browser selector exempt only age expiry; omitted API/CLI mode is strict. Bundled original Nov8 opens deliberately as HISTORICAL ANALYSIS / NOT CURRENT, with capture, expiry, age, collection-only label and verdict provenance. Exact imported UTF-8 text is retained across mode changes and export; originals are not edited or resealed. Every mode retains integrity/origin/window/future/order/control/binding checks. Failed input clears answers, evidence and export; no raw-only bypass. Strict expiry while open clears acceptance; historical requires explicit revalidation.

## Public inputs

- `docs/acceptance/control-fix-20261108/incident.json` — exact bundled Nov8 original.
- `docs/acceptance/recording-20261115/incident.json` — earlier public Nov15 original, NOT the later recording pack.
- Unchanged original bytes/seals are checked in tests and against baseline Git. No private later incident pack was opened or published.

## Verification

- `node --test tests/incident_pack/*.test.js`: 105 passed, 0 failed/skipped (70 existing + 35 historical core/CLI regressions).
- Python full suite: 140 total, 132 passed, 8 existing optional native/demo skips; no suppression. Historical Node suite is now included in Python/CI entry point.
- Dates: Nov16, exact expiry and ±1ms, Dec15 19:00 UTC deadline and Jan15 2027. Both originals tested; no date edits.
- Actual Chromium: **PASS at 360/520/768/1280 × 900**, both original packs, date matrix, four queries, exact byte export, strict/historical transitions, expiry while open, keyboard/reset/reload, origin filter and fail-closed negative paths. Zero page errors, zero outbound requests and zero horizontal overflow. `browser-observations.json` contains the observations; `historical-browser.cjs` is the runnable harness. Narrow screenshot visually inspected locally; no media published.
- Documentation/link lint: PASS, 9 surfaces / 131 local links / 9 chronological host receipts. Unchanged dry-pack validator PASS (232 planned words / 160 planned seconds; not new media). No-SDK hygiene and git diff whitespace checks PASS.
- Implementation milestone pushed: `6bbc9a0`; final documentation tip and exact-tip GitHub CI are reported to the parent after push.
- Local verification: Node v24.22.1; cached Chromium 1243 ARM64 via installed playwright-core. CI uses Ubuntu host workflow.

Browser runs use installed playwright-core and cached non-snap Chromium. Snap Chromium first failed file access (ERR_ACCESS_DENIED); no product change or HTTP server workaround. Initial matrix harness incorrectly waited for VALID/UNKNOWN after Reset (which correctly says No pack loaded); corrected the wait, not product acceptance.

## Limits and non-actions

HOST software/browser tests only; native_rerun:false; £0. No QEMU, SDK/licence, native/core C, safety/C6, media creation, upload, deployment, repository visibility or Devpost edit. Devpost wording is a local owner-review draft only. Cooperative hashes are not signatures/authenticity/attestation. Historical mode does not establish safety, latency, availability, physical hardware, current-tip native acceptance, SSH continuity or SocketCAN. Missing evidence remains UNKNOWN. Existing native/evidence/failure and dry-pack hashes are preserved.
