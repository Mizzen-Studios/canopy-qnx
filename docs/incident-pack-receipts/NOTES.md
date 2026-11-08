# Host-only incident desk verification — 2026-11-08

Implementation milestone fe86b4c; subsequent test/receipt commit contains final assertions. Node v24.22.1, existing local Playwright Chromium. No SDK/QEMU/native execution, native mechanism choice, screenshot/audio/video, external browser requests, server, new port, paid resource, deployment or publication.

- node.log: 34 shared schema/query/CLI tests passed (including mutation groups).
- host.log: 138 host tests, 130 passed / 8 skipped. Includes existing historical reference tests and Node wrapper.
- browser.json: real Chromium local-file DOM/action checks at 1280, 768, 520 and 360 by 900. Keyboard HOST simulation, four queries, evidence expansion, actual download + exported pack revalidation, reset, own local pack import, explicit RECORDED_QNX/FRESH_QNX collector labels, corrupt UNKNOWN, reload clears, no horizontal overflow/runtime errors/external requests. These are not physical-device or human first-minute validation.
- SDK/binary guard passed; historical tools/incident_workbench.py --verify-only passed. Frozen viewer/STATUS/REVIEW/assets untouched by this lane.

Preserved initial failures: synthetic fixture originally shared process object aliases, so a generation-mutation test changed both identities instead of one (31/32). Fixture now produces a serialized deep copy; mutation rejects mixed generation. First browser launch used snap Chromium, which refused local hidden workspace file access (ERR_ACCESS_DENIED); rerun using already installed Playwright Chromium succeeded. No permission bypass or serving workaround was adopted.

Native integration remains deliberately unimplemented until sole native probe outcomes. Exact adapter contract and limitations: ../incident-pack.md. All QNX environment, observer independence, subject hashes and native provenance are collector declarations; cooperative binding is not attestation. V1 does not authenticate SSH, rederive byte streams or prove source→binary→image lineage. Native operator must inspect raw receipts. Missing actual native controls/independent traffic cannot be replaced by HOST fixture. Multiple kills require separate bounded packs. No continuous availability/safety/timing guarantee.
