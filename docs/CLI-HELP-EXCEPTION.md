# Authorized CLI help-only exception — 20 November 2026

Owner20Nov10:12 explicitly permits adding compare to CLI usage text. No parsing, validation, comparison, transfer or native behavior changed. FREEZE.json remains byte-exact and retains its original hash, rather than pretending a new freeze occurred.

File: tools/incident_pack/cli.js

- Frozen SHA256: c9b357f685bf0791c4dd83c872c3d0badda52a2f799af102aff02939bf5a84f4
- Help-only SHA256: 4e082a48b8908570e3242b9b311e94857fb4d9a01bc8a377f3085a660442d3e1

At that help-only checkpoint, all other frozen product files and both original public packs matched FREEZE.json. Later separately authorized C/D changes are documented independently. Both original public packs and the original freeze receipt remain byte-exact; append2 leaves the shared transport and timeline implementation untouched.

## Owner10:15 append2 display exception — 20 November 2026

After shared transport C and timeline D, the owner authorized CLI/display/UI/docs-only polish: compare now prints a human table by default, and --json opts into the unchanged compare API result. Validate/query JSON and strict expiry/integrity validators are unchanged. Parsing only adds the display flag; no native, collector, transport, comparison algorithm or validator changed. The portable one-file desk is a generated projection of approved viewer sources and the two immutable public originals; it adds no private evidence. FREEZE.json is NOT repinned.

CLI before append2 SHA256: 4e082a48b8908570e3242b9b311e94857fb4d9a01bc8a377f3085a660442d3e1
CLI after append2 SHA256: f03a01ecc64187e2d9989323c485102fc6f3492271429e7351f3b0b764a2fd35
