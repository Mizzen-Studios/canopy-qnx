# Historical pre-recording dry pack — 9 November 2026

Superseded as demo preparation by the [15 November live recording](acceptance/recording-20261115d/RESULT.md) and [public narrated video](https://youtu.be/f0yBRgMJvfk). The restrictions and recorded:false metadata below apply to this historical dry pack, not the completed recording.

The [line-by-line script](proof-capture/SCRIPT.md), [machine-readable pack](proof-capture/pack.json) and [validation report](proof-capture/report.json) now follow the current native-first recorder/desk journey. Narration: **219 words**, planned **160 seconds**, editorial only, not a recording, rehearsal or QNX timing measurement.

Packaging assets are frozen at private docs tip a8bfd165f3c4e90e4802c4ec1a8b6deb3ab64525. This is an asset snapshot, **not native acceptance**. Original Nov8 recorder source/ELF/IFS/disk bindings and actual raw captures are unchanged. Prior dry-pack assets/script remain in git history; no acceptance receipt is rewritten.

Planned sequence: host-only saved native-first desk → original recorded native SLM/libcan restart and exact traffic → original provenance/control → host-only query/export/UNKNOWN checks → boundaries. **native_rerun:false**. SSH **UNVERIFIED for current recorder packs**; no historical SSH continuity transfers. Host-sim/doctor material is history/out of scope. C6 FAIL / STOPPED; SocketCAN UNVERIFIED; no safety, timing, continuous-availability or full-platform claim.

Validate offline with python3 tools/proof_capture.py. It checks frozen assets, REVIEW mapping, script/report consistency and planned duration below180seconds. Hashes establish identity, not semantic truth or attestation.

**No recording/audio/video capture, no QEMU run, no publication or upload.** Separate Olly recording authorization remains absent; this wave approves script edits only. Everything private, £0. Freeze after host CI and wait for independent review.
