# Private demo draft — CANopy incident workbench

**Draft only. No recording, upload, publication or submission authorized.** Target edit length **2:35**, hard ceiling 2:55 including titles. Editorial timings are not QNX measurements. Narration ~210 words; private rehearsal needed before any separately authorized capture.

Persistent label: “RECORDED NATIVE EVIDENCE — not live telemetry”. Screens: local static workbench and sanitized repository receipts only. Never display SDK/licence/core contents, credentials, account UI or access URLs. Do not start guests, send CAN traffic or rerun C6 for shots. Cuts must not imply continuous availability. Use saved UNKNOWN fixture pages, not mutations of authoritative receipts.

| Edit time | Shot / exact evidence | Narration |
|---|---|---|
| 0:00–0:20 | README, REVIEW and docs/workbench/index.html | “CANopy is a private, read-only workbench for one recorded QNX libcan and SLM experiment. It presents saved evidence, not a live safety dashboard.” |
| 0:20–0:55 | Recorded workbench incident phases; slm-continuity-20261107/receipt.json and serial | “In three recorded trials, the controller identified and killed the managed CAN process. A new process appeared. The saved post-restart capture contains one hundred received and one hundred transmitted frames per trial, checked for order and exact bytes.” |
| 0:55–1:25 | Same receipt, client/server SSH logs and captured main io-sock PID | “During this bounded experiment, the same authenticated SSH connection kept streaming and the main io-sock PID was unchanged. That observation does not establish continuous CAN service, production isolation or general SSH health.” |
| 1:25–1:55 | UNKNOWN fixtures from unknown-review-20261107/ and browser-20261107/NOTES.md; labels at desktop/mobile | “Missing, corrupt or mixed evidence yields UNKNOWN rather than an accepted incident timeline. Saved Chromium checks cover desktop and mobile layouts. This is host-side rendering and rejection evidence, not another native run.” |
| 1:55–2:15 | Separate docs/replay/index.html with HOST SIMULATION label; no live animation needed | “The older replay is a different, explicitly host-only simulation. Its logical clock and model states do not become QNX proof.” |
| 2:15–2:35 | REVIEW binding gaps and capability ledger; STOPPED/UNVERIFIED labels | “Historical driver source and binary identity are not fully bound. SocketCAN remains unverified. The C6 attempt failed and is stopped. No safety, timing, continuous availability or certification claim follows. Independent owner review is next.” |

## Shot evidence index

- Native journey: docs/acceptance/slm-continuity-20261107/{receipt.json,serial.txt}, associated SSH and frame artifacts indexed in docs/review-claims.json. Recorded image84fc4eda34654854333cf71320b375f2eedae405a3849475623c179443f616f1 is a receipt assertion, not a new external rehash. Historical tested source commit/driver binary UNVERIFIED.
- Static viewer: docs/acceptance/workbench-20261107.json; docs/workbench/recorded-manifest.json. Generation-time validation only.
- UNKNOWN/browser: docs/acceptance/unknown-review-20261107/ and docs/acceptance/browser-20261107/receipt.json, browser source25ca8cf919e81fa62669f2cb8f813fa2cab536df. Saved screenshots remain external; no new capture authorized.
- Review packet baseline61d11d1d3b316ec31f3e770c1ecbee50977d6924; private packet45fc09219ba0bbb8fda8338c50b9c21e61ad4642. Exact artifact digests and missing historical bindings: docs/review-claims.json.

Do not narrate fixed-settle windows as restart latency. No new functional or runtime evidence is created by this draft.
