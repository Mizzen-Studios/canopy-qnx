# CANopy — QNX incident recorder and comparison desk

Record a bounded CAN driver restart, then inspect saved traffic and control evidence locally. [Watch the narrated demo (2:42)](https://youtu.be/f0yBRgMJvfk).

Compare the two public saved incidents now (Node.js 22+, checkout root; no QNX):

~~~sh
node tools/incident_pack/cli.js compare docs/acceptance/control-fix-20261108/incident.json docs/acceptance/recording-20261115/incident.json --historical
~~~

The default output is a human-readable table. Add --json for the unchanged machine-readable API result. --historical is an explicit saved-evidence choice, **not** an automatic expiry/integrity bypass; strict validation remains the default when omitted.

## No clone? Save one file and open it locally

[Download the portable incident desk](https://raw.githubusercontent.com/Mizzen-Studios/canopy-qnx/main/docs/downloads/canopy-incident-desk.html) (save as canopy-incident-desk.html), then open that saved file in a modern browser. It is a **single-file bundle**: no archive extraction, clone, Node, server or installation is needed. All scripts, styles and the two authorized public packs are embedded. [Bundle integrity manifest](docs/downloads/manifest.json).

Inside the desk, save **canopy-2026-11-08-original.json** and **canopy-2026-11-15-original.json** using their separate buttons, then select those files for comparison. Downloads preserve the original bytes and hashes; distinct filenames prevent both incident.json downloads overwriting each other. No later private video pack is included. Historical raw evidence can retain old lab paths; those are not instructions to access a machine.

## Five-minute HOST ONLY judge path

No QNX hardware, SDK, guest image, QEMU, server or upload required. From this checkout with Python 3 and Node.js 22+:

1. Open [the local incident desk](web/incident-pack/index.html).
2. Import either public saved pack: [8 November](docs/acceptance/control-fix-20261108/incident.json) or [15 November](docs/acceptance/recording-20261115/incident.json).
3. Select historical analysis and inspect recovery/raw evidence. These saved observations are **HISTORICAL / NOT CURRENT**, never live health. Explicit historical mode also works after their capture windows expire (8 / 15 December 2026); strict mode rejects packs after expiresAt; corrupt, mixed or missing evidence remains UNKNOWN in either mode.
4. Run the comparison command above, or use the local desk’s two-file comparison.

Both genuine originals record matching 100 RX / 100 TX. Loss-positive examples are HOST synthetic tests, not actual QNX loss. Observations outside the bounded capture remain UNKNOWN. Historical mode never refreshes dates, seals or integrity requirements.

The video's later Nov15d pack is **PRIVATE**, not bundled for this path; publication and access are NOT authorized. The two links above are the only public packs offered here. No private pack is needed for judging.

## Evidence at a glance

| Evidence route | State |
|---|---|
| Recorded journey | Bounded source-bound observations; not current live health. |
| HOST checks | 166 Python tests (158 passed / 8 skipped), 182 Node passed; not native acceptance. |
| Native / reproduction scope | [Complete current status and limits](STATUS.md); separate licensed setup required. |
| Repository | PUBLIC; earlier private-state wording is stale. |

**Demo in QEMU; not a safety or latency claim.** Saved source-bound observations are not current-tip native PASS, hardware validation, attestation or continuous availability.

[Pack / CLI contract](docs/incident-pack.md) · [Capability ledger](docs/capabilities.md) · [Dated history](docs/HISTORY.md) · [Path preservation policy](docs/PATHS.md).

Maintainer HOST checks (longer than the judge path):

~~~sh
python3 -m unittest discover -s tests -v
node --test tests/incident_pack/*.test.js
python3 tools/claim_lint.py
sh scripts/check-no-sdk.sh
~~~

Apache-2.0. No licensed SDK, image, secret or binary is distributed. Native reproduction needs an existing legal setup and separate authorization; this path starts no guest.

## Why QNX

QNX SLM supervises the CAN driver process; the recorded experiment binds its changed PID, libcan RX/TX bytes and finite slog2/control observations. The HOST desk makes those source-bound observations inspectable, not live monitoring.

## How we used AI

Developed with an AI coding agent under human direction: implementation, tests, documentation and evidence review were AI-assisted. HOST checks and recorded native receipts support only their stated scope; AI output is not independent human learner validation, attestation or QNX acceptance.
