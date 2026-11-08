# Structured cofailure correction — 2026-11-08

P1 independent review reproduced before repair in initial-failure.json: changing the v1 control identity to the surviving service still returned isolation OBSERVED. This failed acceptance is preserved, not native evidence. first-tests.log preserves the first failing host run (including an editing-script syntax failure); second-tests.log preserves an intermediate fixture mismatch. Final outcomes are separate.

## Contract

canopy.incident/2 is an explicit compatibility break: v1 imports return UNKNOWN, never quietly accepted/upgraded. Historical viewer, original native-recorder incident.json, logs and pins are untouched. Control data now requires exactly two distinct named co-located members with exact shared name/PID/generation/domain, distinct before/after observation bindings, actual SIGKILL trigger, observed process termination, and a separate exact-identity survivor before/after pair. References, ordering, independence, shared identity and absent/observed outcomes are checked. Control trigger kills are distinguished from the one main-incident kill; control survivors cannot substitute for the main-incident survivor. CLI and UI share this validator/query. Isolation citations include actual control member/fault/survivor events, not just the label.

## Actual native basis (no rerun needed)

Adapted incident.json is a new v2 replay of ../native-recorder-20261108/serial.txt, receipt.json and traffic1.json, with the original source/binary/image/disk receipt text preserved verbatim from the original pack. Source raw SHA256 1fe63c32e4bedf530646189d17288ea8987ccbea21e7740c73809d5f90ce961a.

Serial lines 497–505 show observer-thread samples 0,1,2 at PID2465811, ready, separate parent PID2461712 targeting2465811, actual waitpid signal9, EOF256, zero post-kill co-located output, then three parent post-kill observations. native/prereq_containment.c SHA256 074b043ba12e6e1125dd33491725019317eb886ada072020e8869f5695b1d6e4 matches the bound source map. It explicitly creates the observer pthread inside the worker child, main joins it, and parent kill/waitpid/pipe EOF establish process-wide termination. Thus worker-main and observer-thread shared that process and both ended; these are source-defined roles, NOT invented TIDs or independent thread-death probes. Adapter requires this exact known source topology digest; unknown/missing topology or incomplete/ambiguous actual samples/fault/survivor yields no cofailure event, isolation UNKNOWN. Run-scoped generation labels are adapter identities for this bounded known child lifetime, not OS-reported generation counters.

Actual main incident remains dev-can-linux278546 →331794, independent ordered byte-exact100RX/100TX, io-sock163853 before/after. CLI validation reports VALID and four bounded queries OBSERVED. This is a process-cofailure contrast, not uninterrupted availability, security/adversarial isolation, safety, timing or native C6 proof. No QEMU/SDK was started and no native facts were added to raw logs. Missing per-thread TIDs are not required for the bounded process-wide termination claim; no per-thread timing/continuity claim is made.

## Verification

- contract.log: 59 Node tests pass, including preserved actual-native replay equality, unrelated surviving control, wrong PID/generation, missing/ambiguous members, mismatched trigger/termination/survivor, v1 UNKNOWN, modified-copy actual raw negatives and unknown native topology. Artificial/modified copies are explicitly tests, never native evidence.
- host-final.log: complete SDK-independent host suite (result at end). Node core/native regression suites now both included in the host entry point.
- browser.json: actual Chromium local file import at1280×900 and360×900; exact adapted native pack four queries + control citations, unrelated surviving control UNKNOWN, absent control isolation UNKNOWN, v1 UNKNOWN, no overflow/errors/external requests. No screenshot/audio/video/server. browser-existing.json: original full browser suite at1280/768/520/360 passes.
- receipt.json binds tested source/content and proof bytes. Native receipt lineage and historical pins unchanged. No parent-owned STATUS/REVIEW/claimlint/reviewtools/proofpack edits.
