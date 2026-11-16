# CANopy safe queued fixes — 16 November 2026

Scope: owner-authorized mobile layout and documentation only, based on main `82c9b52fa6cde6043ef1ed1340ca4b14958e86f9`. **Host-only verification; native_rerun:false.** No new native acceptance.

## Changes

- Existing question/answer and evidence sections now precede secondary import/provenance tools. Compact opening retains recorded / not-live / not-current-tip and safety/timing/availability limits before the answer. IDs, application logic, schema, validation, expiry and bundled pack bytes are unchanged.
- README now agrees with the incident-pack Node22+ contract. Verification used installed Node24.22.1 (satisfies22+), Python3.12 and Playwright1.58.2/real headless Chromium; no dependencies installed.
- Clean-copy host instructions create `.openclaw` before output redirection; build instructions create external `$CAN_OUT` before opening its log. No SDK command was executed.
- Native-recorder guide distinguishes historical swap wording and the older collector source/1GiB recipe from the separately bound frozen Nov15 recording: host2GiB, swap0, CPU100%, nice15, guest512MiB/1vCPU, TCG256MiB. No actual cap, collector or controller change.

## Browser evidence

Reproduce: `node tests/incident_pack/browser.cjs` with existing Playwright/Chromium. [Machine-readable receipt](safe-browser.json). Local file URLs only, no screenshots or recording. At1280/768/520/360 ×900, all four recorded answers, all four HOST answers, keyboard activation, cited evidence opening, keyboard raw-artifact expansion, export/download/validate/reimport, reset, own-file import, wrong-origin and corrupt UNKNOWN, reload, no horizontal overflow, no JS errors and zero outbound requests passed.

At360px, the complete selected answer occupies y455.95–623.94 (killed), y455.95–673.53 (recovery), y455.95–648.73 (survivors), or y455.95–747.92 (isolation): each fits within900px, versus the council baseline Ask start2057px. These are rendered-document coordinates, not a human usability study or accessibility certification.

## Checks

- Full Python discovery:140 total,132 passed,8 optional skipped, zero failures.
- Full Node incident-pack suite:70 passed, zero failures/skips.
- `tools/proof_capture.py`, `tools/review_claims.py`, `tools/claim_lint.py`, no-SDK staged/worktree guard, HOST_SIM budget fixture and `git diff --check`: PASS. Derived review/claim inventories regenerated, not historical acceptance receipts.
- Clean archived checkout with no `.openclaw` directory: documented mkdir → fixture output → validate → recovery query PASS (synthetic HOST_SIMULATION only). External-output mkdir/redirection fix inspected against the existing builder; no build attempted.
- Historical proof-capture HTML already uses `git-show-at-accepted-tip`; its old HTML digest is still checked against its existing frozen Git snapshot. No native pin, packaging snapshot, failure, historical receipt or pack was repinned.

## Footage and remaining decisions

The real Nov15 footage contains stale static “saved8November” boilerplate while a fresh pack was being imported. Current desk wording was already corrected at `1227c76`; this layout change preserves that correction. Editing the desk cannot repair pixels in existing footage. No video was altered, generated, uploaded, re-recorded or reassessed here.

Strict expiry is unchanged: the bundled Nov8 pack expires8December2026 16:48:41Z. Archive mode, comparative/loss analysis, another recording and any private fresh-pack publication still require the owner decisions recorded in SCORECARD.md. The private Nov15d incident pack was NOT copied or published.

No QEMU, SDK/licence/media/Devpost/YouTube/visibility/outreach/spend work. C6 FAIL/STOPPED, guest_query native NOT_RUN, SSH/SocketCAN UNVERIFIED; no safety or latency claim. Existing unrelated untracked `.openclaw/` retained. Parent owns independent verification; exact pushed-tip CI is reported separately with the final handoff rather than inventing a self-referential commit hash here.
