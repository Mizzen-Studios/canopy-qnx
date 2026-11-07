# Private proof-capture DRY PACK

No recording or audio capture. Separate Olly OK required. No publication/upload authorized.

Frozen evidence: 79912ef4ab2a738263d1ea22d42210d722182f35
Exact whitespace narration word count: 190; planned 155 seconds (not measured).
C6 FAIL / STOPPED; SocketCAN UNVERIFIED. Historical native and host-only frames remain separate.

## L01 — 0–20 seconds · host-only
Claim: Read-only static workbench presents recorded native libcan/SLM evidence, not live telemetry or safety.
Planned frame: README, REVIEW and docs/workbench/index.html; planned local file view only, not live capture
Narration: CANopy is a private, read-only workbench for one recorded QNX libcan and SLM experiment. It presents saved evidence, not a live safety dashboard.
Frozen files: docs/workbench/index.html SHA256 5282e9f446f35a2b48679c26a349deeed533f7cbc756e39bfb2f803df1c57408, docs/workbench/recorded-manifest.json SHA256 36f4c42e48866ba3871b9254a72b1f2d2348b9cb5fc183c72c2da34ee7dc0efa
REVIEW boundary: Incident viewer / corrupt, missing, mixed rejection / Chromium

## L02 — 20–55 seconds · recorded native QEMU observation
Claim: Three recorded positively identified managed CAN PID kills/restarts with100RX/100TX ordered exact bytes per post-restart trial.
Planned frame: Recorded workbench incident phases; slm-continuity-20261107/receipt.json and serial; planned local file view only, not live capture
Narration: In three recorded trials, the controller identified and killed the managed CAN process. A new process appeared. The saved post-restart capture contains one hundred received and one hundred transmitted frames per trial, checked for order and exact bytes.
Frozen files: docs/acceptance/slm-continuity-20261107/receipt.json SHA256 9df1cab467af2785af8461d133e7b2845fc05a5cf8175f00717eb32e1478df56, docs/acceptance/slm-continuity-20261107/serial.txt SHA256 a1fa4f0fd2ac5473507b5ba273f063aea9998a2d28a97df4beb856d5e96a0d88, docs/acceptance/slm-continuity-20261107/traffic1.json SHA256 18f41a42d9deb3f2355747d9f3c598f862d963092f14bf755522427b117b9b21, docs/acceptance/slm-continuity-20261107/traffic2.json SHA256 bfa758c2253d7414ded2a7d049dd342e9bf0fb617dbe6b9e465c4aecd397cfea, docs/acceptance/slm-continuity-20261107/traffic3.json SHA256 aff53bc86bb0c8bb553d7ee38b4f67e00d666e9ec28be83787869ec93fb70c70
REVIEW boundary: authenticated SSH continuity

## L03 — 55–85 seconds · recorded native QEMU observation
Claim: Same authenticated SSH stream and unchanged main io-sock PID during bounded historical observation only.
Planned frame: Same receipt, client/server SSH logs and captured main io-sock PID; planned local file view only, not live capture
Narration: During this bounded experiment, the same authenticated SSH connection kept streaming and the main io-sock PID was unchanged. That observation does not establish continuous CAN service, production isolation or general SSH health.
Frozen files: docs/acceptance/slm-continuity-20261107/receipt.json SHA256 9df1cab467af2785af8461d133e7b2845fc05a5cf8175f00717eb32e1478df56, docs/acceptance/slm-continuity-20261107/ssh-stream.txt SHA256 4d378ab4eacc905a2a309ceb02b66f134faaa05a1c161990c6af77bc3e65c681, docs/acceptance/slm-continuity-20261107/ssh-debug.txt SHA256 7d8f7672b526229cd0019b00518d2ee5a366115c89c7ff04d196ef37f39e0304, docs/acceptance/slm-continuity-20261107/ssh-server.txt SHA256 dbfa92dfdc29f4631cfdf8c7ebc6771ce6a9141ddef276b0b5cc8eeb60962ff5
REVIEW boundary: authenticated SSH continuity

## L04 — 85–115 seconds · host-only
Claim: Missing/corrupt/mixed evidence yields UNKNOWN; saved desktop/mobile browser checks are host-only.
Planned frame: UNKNOWN fixtures from unknown-review-20261107/ and browser-20261107/NOTES.md; labels at desktop/mobile; planned local file view only, not live capture
Narration: Missing, corrupt or mixed evidence yields UNKNOWN rather than an accepted incident timeline. Saved Chromium checks cover desktop and mobile layouts. This is host-side rendering and rejection evidence, not another native run.
Frozen files: docs/acceptance/unknown-review-20261107/missing.html SHA256 1748ab4b2831df42b9fad86641319637cf97f1d937bc033b7cd7fbd5d3df55c7, docs/acceptance/unknown-review-20261107/corrupt.html SHA256 d0dd2e1deeb0217482b3fe68d7595e4885e67986802c7eea916e04ffe56867e0, docs/acceptance/unknown-review-20261107/mixed.html SHA256 d0dd2e1deeb0217482b3fe68d7595e4885e67986802c7eea916e04ffe56867e0, docs/acceptance/browser-20261107/receipt.json SHA256 8d6392815e0c3855d2efefd4a1cf0eda7f564a50d03bd254ca08e5489d6901c5
REVIEW boundary: Incident viewer / corrupt, missing, mixed rejection / Chromium

## L05 — 115–135 seconds · host-only
Claim: Separate replay is HOST SIMULATION; no QNX proof transfers.
Planned frame: Separate docs/replay/index.html with HOST SIMULATION label; no live animation needed; planned local file view only, not live capture
Narration: The older replay is a different, explicitly host-only simulation. Its logical clock and model states do not become QNX proof.
Frozen files: docs/replay/index.html SHA256 e003d6f78ab2517d936567979a8d200d6a209a9a4152db73ee7a305561f14c7b, docs/replay/run.jsonl SHA256 10433ce54c9aa1dedf22e0a5cdb9df0b0a583c15c7af388afb4aae445aabede9
REVIEW boundary: host-only

## L06 — 135–155 seconds · UNVERIFIED boundaries
Claim: Historical driver source/binary binding incomplete; SocketCAN UNVERIFIED and C6FAIL/STOPPED; no safety/timing/availability acceptance.
Planned frame: REVIEW binding gaps and capability ledger; STOPPED/UNVERIFIED labels; planned local file view only, not live capture
Narration: Historical driver source and binary identity are not fully bound. SocketCAN remains unverified. The C6 attempt failed and is stopped. No safety, timing, continuous availability or certification claim follows. Council acceptance is conditional; native feature scope is frozen. Recording and audio need separate Olly approval.
Frozen files: docs/capabilities.json SHA256 d3cbf3e8325320858e9cf4c1eb33d474a5ee635a01d3977c0928c2270b8da1a8, docs/acceptance/safestop-focused-failure-20261107/receipt.json SHA256 adf790f90acabfbfbaaf2620037ced5f0a4c3aab401148d0f5eaaffbf75f70f0
REVIEW boundary: UNVERIFIED

