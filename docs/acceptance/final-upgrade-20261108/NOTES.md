# Final upgrade verification — 8 November 2026

Clean committed HOST checkout: f99dcf13d101f4bb967d024f41f9b178720f469e. 130 PASS / 8 SKIP. Receipt identifies the tested revision; this subsequent archival commit is not that tested revision. Native executions remain bound to their original source/ELF/IFS/disk receipts, never repinned to current host packaging.

Independent implementation recheck passed all four assigned P1/P2 fixes, 38 bound file hashes and actual browser interactions. See independent-REPORT.md. This is not council acceptance, a full audit or a native rerun. Initial failures are retained separately; test counts are observed results, not objectives.

CANopy: fresh bounded recorder run in ../native-recorder-20261108/; current v2 replay in ../control-fix-20261108/ derives unchanged raw observations. Original v1 is intentionally UNKNOWN in current validator. Initial CI and clean-clone failures exposed a missing test scratch parent; b0e6f12 plus f99dcf1 create each parallel suite scratch parent independently, without product/native changes or weakening assertions. No new SSH continuity; before/after survivors are not availability guarantees.

recorded:false. C6 STOPPED, SocketCAN UNVERIFIED, sshd internal cause UNVERIFIED. No SDK binaries/images/secrets, media capture, publishing/deployment or spend. Fresh f99dcf1 clone host and Node suites PASS; post-suite inventory correctly detected changed test hashes, which are regenerated in the subsequent packaging revision. This is preserved as chronology, not hidden. New council inspection remains pending.
