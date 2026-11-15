# Private proof-capture DRY PACK

No recording or audio capture. Separate Olly OK required. No publication/upload authorized.

Packaging asset snapshot (not native acceptance): e764551aad66624b723a924b46916af7ba13cfde
recorded: false; script-only packaging refresh, no native rerun. Historical receipt source/build pins are unchanged.
Exact whitespace narration word count: 232; planned 160 seconds (not measured).
C6 FAIL / STOPPED; SocketCAN UNVERIFIED. Historical native and host-only frames remain separate.

## L01 — 0–25 seconds · host-only
Claim: HISTORICAL PRE-RECORDING DRY PACK (9 November 2026), not the completed screencast. See [15 November live run](../acceptance/recording-20261115d/RESULT.md) and [public narrated video](https://youtu.be/f0yBRgMJvfk). All no-recording/private gates in this script apply to that historical dry-pack checkpoint. Native-first desk presents unchanged saved QNX v2 pack; native_rerun:false.
Planned frame: Local saved desk web/incident-pack/index.html plus original v2 pack and host-browser receipt. Label host-only rendering of recorded native evidence; no guest or live session.
Narration: CANopy records a bounded QNX incident and makes the saved evidence inspectable. The local desk opens the original native pack. This screen is host software presenting a recorded capture, not live telemetry or a new QNX run.
Frozen files: web/incident-pack/index.html SHA256 8cbb63fad54c41b0be5e3d08afafcc1843b91609bfb3b12cb4083683a14384bf [git-show-at-accepted-tip], docs/acceptance/control-fix-20261108/incident.json SHA256 ced63c778d105bfa7a4a736e5d195fd6dcb65740201a7599d95edb8e9a47da93 [current file equals packaging snapshot], docs/acceptance/native-first-20261108/receipt.json SHA256 0a2b0b84c04698a21de66df37f7c4050ca79d44e1d50efde6012e596af1047ed [current file equals packaging snapshot]
REVIEW boundary: host-only native-first desk

## L02 — 25–65 seconds · recorded native QEMU observation
Claim: Original Nov8 scoped native recorder PASS: SLM restart, byte-exact100RX100TX, finite slog2 and actual co-located control.
Planned frame: Local saved evidence only: docs/acceptance/native-recorder-20261108/receipt.json, docs/acceptance/native-recorder-20261108/serial.txt, docs/acceptance/native-recorder-20261108/traffic1.json, docs/acceptance/native-recorder-20261108/control-slog.txt. Label recorded native or host-only; never show a live session or run a guest.
Narration: In the original source-bound native capture, the separate recorder observed the managed CAN driver stop and restart. Independent traffic checks compared one hundred received and one hundred transmitted frames in order and byte for byte. Finite slog phases and the co-located death control are retained with their raw observations.
Frozen files: docs/acceptance/native-recorder-20261108/receipt.json SHA256 014961af46955d7ba0517d176f7532f7de019f9d21f01164d60aa01deb04305c [current file equals packaging snapshot], docs/acceptance/native-recorder-20261108/serial.txt SHA256 1fe63c32e4bedf530646189d17288ea8987ccbea21e7740c73809d5f90ce961a [current file equals packaging snapshot], docs/acceptance/native-recorder-20261108/traffic1.json SHA256 18f41a42d9deb3f2355747d9f3c598f862d963092f14bf755522427b117b9b21 [current file equals packaging snapshot], docs/acceptance/native-recorder-20261108/control-slog.txt SHA256 a72b39ee4be1568e5d27e5c866d171db3040dfad6081de203caebb6c84aea933 [current file equals packaging snapshot]
REVIEW boundary: SLM-managed driver kill/restart

## L03 — 65–100 seconds · recorded SDK build / native NOT_RUN
Claim: New guest query qcc ELF build PASS; native NOT_RUN due measured stock mkifs kernel relink OOM, not fresh runtime proof.
Planned frame: Saved Nov10 measured receipt, stage logs and memory census only. No guest or live session. Original Nov8 bindings stay separate.
Narration: The new query face uses explicit Neutrino message passing. Its three application ELF builds succeeded. The unchanged capped SDK guest then exhausted memory while mkifs relinked the existing kernel. The image stayed empty. This measured blocker is not native acceptance of the new query or a fresh recorder run.
Frozen files: docs/acceptance/control-fix-20261108/receipt.json SHA256 4ba52fd8b40023c8751cb3df6ebd866dbbdd3b03219ed7fa62ca0ae28e80a499 [current file equals packaging snapshot], docs/acceptance/control-fix-20261108/incident.json SHA256 ced63c778d105bfa7a4a736e5d195fd6dcb65740201a7599d95edb8e9a47da93 [current file equals packaging snapshot], docs/acceptance/native-recorder-20261108/build-projection.log SHA256 b587532fc4c615a3aa9946464e4f256ef1cf1c89bf7b2d1d96b7c14b0494adb4 [current file equals packaging snapshot], docs/acceptance/query-retry-20261110/receipt.json SHA256 af6986cf176a2a88d93a4a9c5510814675751596035d7996f9abb7d81a7e2a33 [current file equals packaging snapshot]
REVIEW boundary: qcc ELF build PASS

## L04 — 100–130 seconds · host-only
Claim: New same-pack guest query and slog2 adapter/desk host tests only; no fresh native pack or new browser acceptance.
Planned frame: Saved host test and measured blocker receipt; original browser receipt explicitly historical. No live or newly accepted native pack.
Narration: Host tests exercise the new same-pack query and slog viewer, with missing, corrupt, mixed and wrong-origin inputs rejected as UNKNOWN. This is host validation using fixtures, not new QNX behavior or a completed browser acceptance journey. The cold desk still opens the original recorded pack.
Frozen files: docs/acceptance/native-first-20261108/receipt.json SHA256 0a2b0b84c04698a21de66df37f7c4050ca79d44e1d50efde6012e596af1047ed [current file equals packaging snapshot], docs/acceptance/native-first-20261108/footer-browser.log SHA256 bc3fd63f7d03957396fbd3cd22de8eccd8c4dc5bf66c6c18e5ade21141f14842 [current file equals packaging snapshot], docs/acceptance/query-retry-20261110/receipt.json SHA256 af6986cf176a2a88d93a4a9c5510814675751596035d7996f9abb7d81a7e2a33 [current file equals packaging snapshot]
REVIEW boundary: host tests only

## L05 — 130–160 seconds · UNVERIFIED boundaries
Claim: Current-pack SSH UNVERIFIED; historical host-sim/doctor and C6 out of scope, C6 STOPPED, SocketCAN UNVERIFIED.
Planned frame: Local saved evidence only: docs/acceptance/native-recorder-20261108/NOTES.md, docs/acceptance/native-first-20261108/NOTES.md. Label recorded native or host-only; never show a live session or run a guest.
Narration: SSH remains unverified for the new source. Original native results keep their original bindings. C6 is stopped, SocketCAN unverified, and pathname policy blocked. No platform repair, swap, cap increase or single-host retry followed. No safety, timing or continuous-availability claim is made. This is a private script only; nothing was recorded or published.
Frozen files: docs/acceptance/native-recorder-20261108/NOTES.md SHA256 d5cd11538ec878e2229601f5e1b55819a7c6f7e0bfb58debb0551516fa983c40 [current file equals packaging snapshot], docs/acceptance/native-first-20261108/NOTES.md SHA256 8ca64b543fef4df494a4cdfffe1f48de3a41015c86a91febbe4434a8ab63b660 [current file equals packaging snapshot]
REVIEW boundary: C6/native safety STOPPED

