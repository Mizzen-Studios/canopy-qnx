# Authorized CLI help-only exception — 20 November 2026

Owner20Nov10:12 explicitly permits adding compare to CLI usage text. No parsing, validation, comparison, transfer or native behavior changed. FREEZE.json remains byte-exact and retains its original hash, rather than pretending a new freeze occurred.

File: tools/incident_pack/cli.js

- Frozen SHA256: c9b357f685bf0791c4dd83c872c3d0badda52a2f799af102aff02939bf5a84f4
- Help-only SHA256: 4e082a48b8908570e3242b9b311e94857fb4d9a01bc8a377f3085a660442d3e1

All other frozen product files and both original public packs must still match FREEZE.json. The additive transport helper is untouched.
