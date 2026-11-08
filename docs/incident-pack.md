# Bring your own incident pack v2

Open [the incident desk](../web/incident-pack/index.html) directly from a local checkout in Chromium. No server, port, SDK, native process, upload or network. Choose JSON, select a question, follow evidence, export or reset. HOST simulation is synthetic, never native evidence. State clears on reload. Export contains imported text: review confidential observations before sharing.

## Run locally

    node tools/incident_pack/fixture.js > .openclaw/host-pack.json
    node tools/incident_pack/cli.js validate .openclaw/host-pack.json
    node tools/incident_pack/cli.js query .openclaw/host-pack.json recovery
    node --test tests/incident_pack/core.test.js

Node 22+, no npm dependencies. CLI exits 0 for VALID structure/bindings, 2 for UNKNOWN. Answers can remain UNKNOWN on a VALID pack. Optional browser checks with already available Playwright/Chromium: node tests/incident_pack/browser.cjs. No downloads, screenshots/audio/video, server or external requests.

## Exact schema

Executable closed-field schema: [core.js](../tools/incident_pack/core.js), shared by CLI/browser. Complete runnable synthetic producer: [fixture.js](../tools/incident_pack/fixture.js). Unknown fields/version fail UNKNOWN. IDs: 1–64 ASCII alphanumeric/underscore/hyphen. Digests: lowercase 64-hex SHA-256. UTF-8 only; duplicate JSON keys rejected.

Root fields: schema (canopy.incident/2), collector, run, bindings, artifacts, events, seal.

- collector: id, version, mechanism (IDs). Mechanism is descriptive, never selected or executed by importer. No slog2/secpol/dual-versus-in-process mechanism assumption.
- run: unique id; environment HOST_SIMULATION, RECORDED_QNX or FRESH_QNX; capturedAt/expiresAt date strings. Maximum 30-day window; capture at most 5 minutes in future. Expired input UNKNOWN. Labels are collector declarations, NOT independent QNX proof. FRESH_QNX denotes a newly collected bounded run, never a live connection.
- bindings: source, binary, image, disk: four distinct artifact paths with corresponding roles.
- artifacts: 1–32 records, each path, role, runId, text, sha256 (text digest), subjectSha256 (digest of underlying source set, executable, image, disk or raw observation stream). Roles source/binary/image/disk/observation. Native text receipts must record subject-digest computation, source revision + dirty content digest, build invocation/receipt linked input hashes, image/disk lineage and boot/run identity. Actual SDK/binaries/images/disks are NOT embedded. Importer checks text integrity and digest format, NOT native provenance. Host fixture descriptors explicitly are not real binaries/images.
- events: 1–2048 records: id, seq (zero-based consecutive), at (monotonic relative milliseconds, <=1 day), runId, kind, process, observer, evidence, data.
- process: name, positive integer pid, generation, domain. Other fields IDs. PID reuse is not a generation. Same generation must retain identical identity. Domain identifies a boundary, not proof of security enforcement.
- observer: name, generation, independent boolean. Self-generation cannot claim independence. Independence is collector provenance, not attestation. Native receipts must identify actual separate observer and collection channel.
- evidence: 1–8 path/line objects pointing to embedded observation text (1-based). Displayed escaped, never fetched/executed.
- data by kind (closed fields):
  - process/interruption/recovery: state observed or absent.
  - kill: signal SIGKILL; actual target/result, not intended command.
  - traffic: direction RX or TX, count exactly 100, positive bytes <=1 MiB, expectedSha256, observedSha256, ordered boolean. Adapter defines canonical ordered frame encoding in evidence and preserves expected/actual streams or derivation. Independent observer must actually compare 100 frames each direction. Importer compares digests, not unavailable hardware.
  - control: mode in_process, outcome cofailure_observed or not_observed; members (exactly two distinct named members, each name/process/before/after), trigger, termination, survivor (before/after event IDs). Both members must carry the exact control process identity including PID/generation/domain and distinct observed-before/absent-after process event IDs. The SIGKILL trigger and independently observed process termination must match that identity, be ordered after member-before observations and before member-after observations. The separate survivor must retain exact identity, differ in PID/generation/domain, and have independent before/after observations around that control fault. All referenced events precede the summary. Process-wide termination can establish both member absences; do not invent per-thread telemetry. Missing/ambiguous/mismatched bindings invalidate the pack to UNKNOWN.
  - optional ssh: session, phase before/after, challenge, responseSha256. After requires same session, later event and distinct challenge. Emit only actual same-session challenges, never serial or reconnect disguised as SSH. V2 displays evidence but offers NO SSH continuity verdict or authenticated session proof.

seal = SHA-256 of recursively key-sorted compact JSON root without seal, preserving array order, UTF-8. Use exported seal() to avoid cross-language canonicalization ambiguity; producer numbers finite safe integers. Artifact text hashed without newline normalization. Cooperative hash binding is NOT signature, cryptographic attestation, authenticity or adversarial-host proof. A producer able to rewrite the pack can forge it.

Limits: 2 MiB input, nesting <24, 128 Ki characters/artifact, 1 MiB total artifact UTF-8, 32 artifacts, 2048 events, 8 references/event, paths <=180 characters. No absolute paths, traversal, backslashes, empty segments or duplicates. Embedded-only: no archive/extraction or artifact filesystem dereference. CLI reads one regular local file, rejects symlink path components and uses O_NOFOLLOW on leaf. Ancestor checks are not race-proof against a malicious concurrent filesystem actor; importer is not an adversarial-host sandbox. No URL fetching or shell execution.

Failure invalidates all answers to UNKNOWN. Missing control/observation keeps specific answers UNKNOWN. Preserve failures; recover with a complete matching current pack, not by rehashing edited historical evidence.

## Queries

Exactly one main-incident kill per query scope; validated control trigger kills are excluded. Control-process and control-survivor snapshots cannot substitute for the main incident survivor. Recovery requires independent interruption after kill, replacement generation in same domain, then independent ordered matching 100 RX and 100 TX. Survivor means independent same-generation before/after snapshots, not uninterrupted operation. Isolation contrast additionally requires separate-domain survivor and explicit in-process cofailure control. PID change alone is insufficient. Multiple kills currently UNKNOWN: use bounded separate incident packs. No continuous availability, safety, timing, security isolation or native C6 guarantee.

## Native adapter and new collection

The bounded slog2/serial/libcan adapter is tools/incident_pack/native.js. Follow [native-recorder.md](native-recorder.md) to build and collect a new incident, then validate and import its exact JSON. Do not modify historical receipts or treat HOST fixture as native. Bind collector/version, boot/run, source/build, binary/image/disk digests in textual receipts; keep licensed inputs/secrets outside git. Include actual process generations, actual kill and interruption/recovery. Emit independent traffic and explicit in-process control only when actually proven; otherwise preserve UNKNOWN. Serialize with seal(), validate CLI and import same exact file in UI. Retain raw receipt hashes and review actual native provenance: host validation cannot verify QNX ran.

The importer itself provides no SDK/QEMU operation. Native collection is a separate explicit command and never starts from the browser. [Historical viewer](incident-workbench.md), pins and failures remain separate unchanged. No C6/safe-stop/heartbeat/actuation/SocketCAN work.

## Design and verification scope

Incident desk: paper #f2f6fa, ink #17324c, blue #1c537d, line #b5c6d6, warning #764100, white #fff. Local Trebuchet/Arial; two-column opening then import → question → cited observation. Rejected generic repeated-card dashboard/monospace telemetry wall: first-minute task is a decision, not monitoring. Single-column mobile, explicit labels, focus outlines, 48px controls, live validation feedback; no fonts/network/motion. Automated DOM checks are not human usability or accessibility certification.

## v1 compatibility break

V2 rejects v1 as UNKNOWN (no silent upgrade or legacy acceptance). Historical packs/viewer/pins remain untouched. Re-adapt preserved original native inputs with the v2 adapter; emit structured controls only when raw records and known collector topology establish them. New accepted replay and source-bound tests: [control-fix-20261108](acceptance/control-fix-20261108/NOTES.md).
