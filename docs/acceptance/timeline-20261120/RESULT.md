# ItemD: recorded visual timeline — HOST ONLY

Owner20November10:14 authorized a UI-only exception after polish baseline a54445e2ee267622da8201aba7a1c40c5505f26a. This changes web/incident-pack presentation and adds view-only helper/tests. It does not revise FREEZE.json or claim new native acceptance. Native sources, core validator, expiry/evidence rules, original public pack bytes, bundled example and pins are unchanged. Recording remains HOLD; no QEMU/SDK/lease/media attempt.

Design: retain existing ink #17324c,paper #f2f6fa,blue #1c537d,line #b5c6d6,alert #764100 and Trebuchet type. A quiet left-aligned evidence rail sits AFTER incident questions, not a decorative hero. Chronological positioning uses accepted pack event.at values, preserves original tie order and stable event IDs. Offsets are explicitly collector-declared pack-relative milliseconds, NOT wall-clock timestamps, measured recovery latency or continuous health. These original captures can contain serialized offsets; spacing is not a timing guarantee. Every event and raw path:line link opens its corresponding evidence detail.

Timeline receives only the viewer's already accepted validation result. Import/mode/origin/reset/empty-file/integrity failure and strict expiry clear it alongside verdicts, with no dangling rows. No synthetic-to-native relabelling, extra validation exemption, network request or innerHTML. HOST/SYNTHETIC keeps its own origin label. Malicious strings render as inert text.

Verification:
-180 shared Node tests passed, including2new timeline tests: accepted-only/empty rejection, stable tie ordering, stable IDs, malicious strings and nonmutation.
-Actual HOST Chromium360/520/768/1280 x800: first-screen question action bottoms773.31/712.05/752.88/724.98px; no horizontal overflow, page errors or external requests. Keyboard Enter opens cited evidence. Invalid/corrupt/wrong-origin/empty/reset/expired-strict clearing and malicious DOM inertness passed.
-Existing historical, comparison and diagnostic Chromium regressions passed. Public originals only; no private Nov15d pack.
-Eight first-screen/timeline screenshots inspected at all four widths; original360first-screen failure retained privately, then condensed scope/mode spacing to keep question action fully visible without hiding NOT CURRENT or changing validator behavior.

Proof screenshots/logs remain outside Git at workspace artifacts/private/canopy-timeline-20261120/: first-{360,520,768,1280}.png,timeline-{360,520,768,1280}.png,result.json,node-tests.log,historical.json,compare-independent.json,diagnostic-independent.json. Reproduce with NODE_PATH and CHROMIUM_PATH set to installed Playwright dependencies, PROOF_DIR outside repo, then node tests/incident_pack/timeline-browser.cjs. These are HOST UI proofs, not QNX execution.
