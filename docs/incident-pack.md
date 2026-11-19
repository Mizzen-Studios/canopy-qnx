# Bring your own incident pack — v2 and diagnostic v3

**Nov10 gate:** guest_query ELF qcc build PASS; new native query/recorder/SSH journey NOT_RUN, no fresh same-pack native acceptance. Stock mkifs procnto relink OOM at unchanged caps; [measured blocker](acceptance/query-retry-20261110/NOTES.md). The new guest-query/slog2 viewer is host-tested only. Original Nov8 example and bindings unchanged; SSH UNVERIFIED. No further run authorized by this guide.


Open [the incident desk](../web/incident-pack/index.html) directly from a local checkout in Chromium. No server, port, SDK, native process, upload or network. Cold open loads the original recorded native v2 pack from control-fix-20261108, unchanged and locally bundled. Select a question, follow the actual raw/control evidence, export/reset or import your own JSON. Reset clears the loaded pack; reload deliberately opens the recorded example again. The primary import expects QNX; choose the explicit HOST simulation origin or secondary sample for HOST data. A wrong expected origin fails UNKNOWN. HOST simulation is synthetic, never native evidence. The example is recorded evidence, not a new native run at the current tip. Export retains exact imported UTF-8 bytes (including formatting and line endings): review confidential observations before sharing.

## Historical analysis (19 November)

The bundled example deliberately opens in **HISTORICAL ANALYSIS — NOT CURRENT** mode, even after its unchanged expiry. The selector above the question shows mode, collector-declared capture/expiry, age and expired status. Every verdict includes provenance; original FRESH_QNX means collection-time labeling only, never current-tip acceptance. Switching modes revalidates the same original text, not a reserialized or resealed copy. Strict expiry while open clears verdict/evidence/export; explicitly selecting historical mode revalidates the retained original. Invalid packs expose no raw-only fallback or verdict.

API: `validate(raw, {mode:'historical'})`; omitted mode stays strict. CLI: append `--historical` to validate/query. Both return scope fields including mode, current:false, capturedAt, expiresAt, checkedAt, ageMs, expired, runId, originalEnvironment and original seal on accepted input. Historical accepts only otherwise valid, cooperatively bound observations; hashes are not authenticity or attestation. Future captures, invalid/overlong windows, malformed/duplicate/mixed/corrupt/bad-control/bad-origin packs still fail closed. No date edits, refresh, reseal or inference of safety, availability or latency.

    node tools/incident_pack/cli.js query docs/acceptance/control-fix-20261108/incident.json recovery --historical

[Host-only acceptance and limits](acceptance/historical-analysis-20261119/RESULT.md). The earlier public 15 November pack is distinct from the separately recorded later run; no private pack is made public by this feature.

## Run locally

    mkdir -p .openclaw
    node tools/incident_pack/fixture.js > .openclaw/host-pack.json
    node tools/incident_pack/cli.js validate .openclaw/host-pack.json
    node tools/incident_pack/cli.js query .openclaw/host-pack.json recovery
    node --test tests/incident_pack/core.test.js

Node 22+, no npm dependencies. CLI exits 0 for VALID structure/bindings, 2 for UNKNOWN. Answers can remain UNKNOWN on a VALID pack. Optional browser checks with already available Playwright/Chromium: node tests/incident_pack/browser.cjs. No downloads, screenshots/audio/video, server or external requests.

## Exact schema

Executable closed-field schema: [core.js](../tools/incident_pack/core.js), shared by CLI/browser. Complete runnable synthetic producer: [fixture.js](../tools/incident_pack/fixture.js). Unknown fields/version fail UNKNOWN. IDs: 1–64 ASCII alphanumeric/underscore/hyphen. Digests: lowercase 64-hex SHA-256. UTF-8 only; duplicate JSON keys rejected.

Root fields: schema (canopy.incident/2), collector, run, bindings, artifacts, events, seal.

- collector: id, version, mechanism (IDs). Mechanism is descriptive, never selected or executed by importer. No slog2/secpol/dual-versus-in-process mechanism assumption.
- run: unique id; environment HOST_SIMULATION, RECORDED_QNX or FRESH_QNX; capturedAt/expiresAt date strings. Maximum 30-day window; capture at most 5 minutes in future. Expired input UNKNOWN in default strict validation. Explicit historical analysis exempts only age expiration; all other checks still apply. Labels are collector declarations, NOT independent QNX proof. Known synthetic/native collector contradictions and HOST descriptors relabelled native fail UNKNOWN; this does not detect a producer who forges all compatible declarations. FRESH_QNX denotes a newly collected bounded run, never a live connection.
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

Incident desk: paper #f2f6fa, ink #17324c, blue #1c537d, line #b5c6d6, warning #764100, white #fff. Local Trebuchet/Arial; compact opening then question → cited observation → secondary import/provenance tools. Rejected generic repeated-card dashboard/monospace telemetry wall: first-minute task is a decision, not monitoring. Single-column mobile, explicit labels, focus outlines, 48px controls, live validation feedback; no fonts/network/motion. Automated DOM checks are not human usability or accessibility certification.

## v1 compatibility break

V2 rejects v1 as UNKNOWN (no silent upgrade or legacy acceptance). Historical packs/viewer/pins remain untouched. Re-adapt preserved original native inputs with the v2 adapter; emit structured controls only when raw records and known collector topology establish them. New accepted replay and source-bound tests: [control-fix-20261108](acceptance/control-fix-20261108/NOTES.md).

## Council browser boundary

Council reported its browser connection attempt BLOCKED before any journey executed; that is not a product failure or a parent test result. New local host Chromium receipts are separately recorded, with desktop/narrow positive recorded-native and negative-pack journeys. native_rerun:false for this host-only change. No SSH continuity on the new recorder pack; historical SSH evidence is separate.


## Comparative, loss-aware diagnosis (host software, 19 November)

Open **Compare two captures**, choose both original JSON files and each expected origin, then Compare.

CLI: `node tools/incident_pack/cli.js compare LEFT.json RIGHT.json [--historical]`.
API: `require('./tools/incident_pack/compare').compare(leftRaw, rightRaw, {mode:'historical'})`; omitted mode is strict. API additionally accepts separate `left` / `right` validation options. No API takes prevalidated objects: each original is validated again independently.

Each side retains its own run ID, capture/expiry/check time, mode, origin, seal, source/binary/image/disk bindings and process identities. No events or PIDs are pooled. The same pack is explicitly not independent incidents; a shared run ID with different seals is ambiguous UNKNOWN. Mixed HOST/native comparisons have no shared native conclusion. Historical exempts expiry only; strict expired input remains UNKNOWN.

Diagnosis requires explicit RX/TX expected and actual arrays in embedded RX.txt/TX.txt, with canonical decimal SFF ID and eight lowercase-hex bytes per row. It verifies artifact/subject hashes, event digests, observed counts/bytes, exact-order summary, citation and recovery process. Recorded native input additionally requires the supported serial collector, recovery PID at its cited line, RX observed rows and TX expected command rows matching serial. Host-observed TX remains separately bound in TX.txt; serial commands do not establish TX reception. Missing, conflicting or ambiguous data is UNKNOWN, never a fabricated zero.

Multiset differences respect expected multiplicity: excess known-frame occurrences are duplicates, unknown frames unexpected, deficits missing. Relative order compares shared occurrences; it does not assign causality or exact dropped transmission times. CAN IDs are not implicit sequence counters. Gaps in IDs, silence, snapshots and uncaptured intervals establish no loss. Resource bounds: two 2 MiB packs, at most512 frames per list and32 Ki characters per traffic artifact, linear-count analysis, existing event/artifact limits unchanged. The v2 event contract still requires100 observed frames. Variable counts require the explicit diagnostic v3 contract below, never a silent v2 relaxation.

Both original public recorded incidents show100 expected/100 observed RX and TX, ordered exact: **no missing frames observed in these finite recorded lists; outside capture UNKNOWN**. No genuine loss-positive incident has been established in this scope. Positive algorithm tests are explicitly HOST/SYNTHETIC, NOT QNX; originals are never resealed. Future real differences are flagged only when the bound recorded evidence meets this contract. Export left/right returns each accepted original's exact UTF-8 bytes, not a regenerated/sealed JSON. Local only, no uploads.

[Item2 acceptance and owner-review draft](acceptance/comparative-analysis-20261119/RESULT.md). Parent independent review required; recommend freezing1+2 for later separately authorized REAL recording. No native execution, private later pack publication, C6 or external edits.

## Diagnostic v3 follow-up — bounded missing frames

Version decision: canopy.incident/3 is additive and explicit; canopy.incident/2 and its native serializer retain their original strict100 contract and byte-identical public packs. A genuine99-frame observation cannot be represented as a v2 traffic event. Do not pad arrays, invent frames, change old receipts or silently upgrade/reseal an original. There is no new loss-positive native capture here. Native v3 serialization is opt-in and **not native-verified**; the default native adapter still emits v2. API: adapt(dir,lineage,{schema:'canopy.incident/3'}); CLI: node tools/incident_pack/native.js CAPTURE_DIR LINEAGE.json --diagnostic-v3. It derives counts, bytes, digests and order from the actual recorded traffic1.json arrays, and requires the exact matching completion lines already in the original serial capture. It does not create completion lines, pad arrays or fabricate a run. Existing originals correctly fail this opt-in because they have no such declarations, and default v2 re-adaptation remains exact. The capture collector has not been modified or run to emit new completion declarations; a future separately authorized collector must record them before v3 can be used natively. Host diagnostic fixtures are not a native producer.

V3 keeps the same closed root, binding, event, artifact, origin, temporal and cooperative seal checks. Its traffic data fields are direction, count, bytes, expectedSha256, observedSha256, ordered, plus **expectedCount, expectedBytes, captureEnd**. Observed count and expectedCount are independently bounded safe integers0..512; bytes=count×8 and expectedBytes=expectedCount×8. Explicit expected and actual lists in RX.txt/TX.txt must exactly match these counts and their independently declared canonical digests, including the SHA-256 of empty UTF-8 for an explicit empty list. Empty lists have headers and final newlines; a blank artifact is not an empty observation. Only standard11-bit IDs and eight-byte frames are supported. Duplicate events, absent direction, raw/summary mismatch or ambiguous process invalidate the entire v3 pack and all four query answers, not just the comparison.

captureEnd is a closed {path,line} observation citation. Its cited line must be exactly the following space-delimited finite-completion declaration, with values matching the same event/run/independent observer and both lists:

    CANOPY_CAPTURE_COMPLETE RUN_ID DIRECTION OBSERVER_GENERATION EXPECTED_COUNT OBSERVED_COUNT EXPECTED_SHA256 OBSERVED_SHA256

The completion artifact itself must be an embedded observation with subjectSha256 equal to its raw text hash. In a native-origin v3 pack this citation must be in serial.txt after the recovery PID and every matching direction frame/command, with actual RX rows matching the observed array and actual TX command rows matching the expected array. TX observed data is separately host-bound, not established by cansend command echoes. No completion declaration may be manufactured from a timeout, blank artifact or absent observer. The declaration is cooperative producer provenance, not authenticity or independent attestation. Without finite completion/observer evidence, zero observations remain UNKNOWN, never an assumption of total loss. Outside the explicit lists remains UNKNOWN.

The shared validate API, CLI validate/query/compare and browser import/comparison all accept v3 through the same full validation. V3 is checked against raw lists and serial provenance **before** query answers are constructed; there is no raw-only or unknown-options bypass. Recovery/isolation100-frame wording still requires actual ordered100 expected and100 observed **in each direction**, plus the original interruption, replacement-generation, independent-observer and control requirements. A one-frame match,99/100 or0/100 cannot earn that verdict. Killed and survivor questions retain their original snapshot semantics.

Default strict expiry and historical-only expiry exemption are unchanged. Future/corrupt/mixed-run/invalid options remain UNKNOWN. Existing2 MiB input, artifact/event limits,512 frames/list and32 Ki characters/traffic bounds stay in force. Full historical and comparative original-pack browser regressions accompany four-width v3 HOST/SYNTHETIC journeys. [Follow-up acceptance and owner draft](acceptance/diagnostic-v3-20261119/RESULT.md); the earlier comparative receipt remains historical and unchanged.
