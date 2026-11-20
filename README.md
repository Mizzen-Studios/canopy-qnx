# CANopy — QNX incident evidence workbench

Record a bounded CAN driver restart, then inspect saved traffic and control evidence locally. [Watch the narrated demo (2:42)](https://youtu.be/f0yBRgMJvfk).

## Five-minute HOST ONLY judge path

No QNX hardware, SDK, guest image, QEMU, server or upload required. From this checkout with Python 3 and Node.js 22+:

1. Open [the local incident desk](web/incident-pack/index.html).
2. Import either public saved pack: [8 November](docs/acceptance/control-fix-20261108/incident.json) or [15 November](docs/acceptance/recording-20261115/incident.json).
3. Select historical analysis and inspect recovery/raw evidence. These packs are expired: **HISTORICAL / NOT CURRENT**, never live health. Strict mode still rejects expired packs; corrupt, mixed or missing evidence remains UNKNOWN in either mode.
4. Compare the two public captures from the repository root:

~~~sh
node tools/incident_pack/cli.js compare docs/acceptance/control-fix-20261108/incident.json docs/acceptance/recording-20261115/incident.json --historical
~~~

Both genuine originals record matching 100 RX / 100 TX. Loss-positive examples are HOST synthetic tests, not actual QNX loss. Observations outside the bounded capture remain UNKNOWN. Historical mode never refreshes dates, seals or integrity requirements.

The video's later Nov15d pack is **PRIVATE**, not bundled for this path; publication and access are NOT authorized. The two links above are the only public packs offered here. No private pack is needed for judging.

## Evidence at a glance

| Evidence route | State |
|---|---|
| Recorded journey | Bounded source-bound observations; not current live health. |
| HOST checks | 145 Python tests (137 passed / 8 skipped), 178 Node passed; not native acceptance. |
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
