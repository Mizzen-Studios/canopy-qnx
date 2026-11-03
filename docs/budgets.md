# Host application budget gates (C11 host-only)

These standard-library checks exercise application budget logic. They do not
establish QNX performance, safety certification, driver correctness, WCET, or
successful target execution. All committed budget fixtures are invented logical
time and source **HOST SIM**, never recorded QNX observations. **HOST VCAN** is
reserved for actual host vcan captures. Genuine target evidence: **none**.

## Strict budgets.yaml v1

Exactly five flat keys are required: version (1), deadline_ms (finite unsigned
decimal), restart_gap_ms (same), overruns (nonnegative integer), byte_exact (true).
No implicit coercion, scientific notation, NaN/infinity, negative values, strings,
nesting, tags, anchors, duplicate/unknown/missing keys, or disabling byte-exact.
Comments and blank lines are supported. Defaults are illustrative app budgets,
not measured results. Equality to a budget passes; exceeding it fails.

## Evidence JSON v1

See tests/fixtures/budgets/host-sim-pass.json for the complete schema.

- version: integer 1; source: HOST SIM or HOST VCAN; target_evidence: none.
- deadline_samples_ms: nonempty list of finite nonnegative observed signal ages
  or deadline durations; CP101 compares the maximum to deadline_ms. The caller
  must provide the complete relevant sample window, not cherry-picked samples.
- restart_chain_ms: all five nonnegative finite durations: death_to_spawn,
  driver_up, ifconfig, canvss, first_frame. CP102 compares their sum to
  restart_gap_ms. These represent sequential nonoverlapping hops in one window.
- overruns: integer count for the capture window; CP103 compares to overruns.
- expected_candump, actual_candump: log CONTENTS (not paths); CP104 compares
  ordered classic CAN frames. Both must contain at least one valid frame.

Missing/empty/wrong-type/nonfinite evidence fails its gate. Invalid provenance
fails every gate. JSON duplicate keys and nonfinite constants are rejected.
Source labels are assertions supplied by the capture producer, not cryptographic
attestation. Never relabel simulated durations as measured data.

Candump supports compact -L and human readable classic CAN, timestamp prefixes,
standard 3-hex and extended 8-hex IDs, zero through eight bytes, and RTR/DLC.
Timestamp/interface differences and hex case are ignored. ID, standard/extended
identity, RTR, DLC, payload bytes, count, duplicates and order must match.
Malformed lines and unsupported FD/error frames fail closed; they are not skipped.
Blank lines are ignored. FD support is not claimed.

## Parent CLI/CI integration API

Import canopy_host.check:

    budgets = load_budgets('budgets.yaml')
    evidence = load_evidence('tests/fixtures/budgets/host-sim-pass.json')
    report = check(budgets, evidence)
    print(render_rustc(report), end='')
    print(render_github_annotations(report))
    summary = render_github_summary(report)
    status = report.exit_code

Report.results contains CheckResult(code, status, message, observed, budget,
path, line); status is pass/fail. report.passed is the aggregate host result;
exit_code is 0/1. report.source and target_evidence preserve the host-only boundary.
parse_budgets(text, path) and compare_candump(expected_text, actual_text) are
also public APIs. The latter returns None for equality or first mismatch detail;
parse errors raise EvidenceError. Input/loading failures must become nonzero CLI
errors: catch EvidenceError, OSError and ValueError, never fall back to defaults.
Library renderers do not write files/environment or execute GitHub commands.
The parent owns root CLI argument handling, summary file writes and CI wiring.
Annotations escape workflow-command injection; summaries escape HTML/table input.
Budget annotation lines follow the actual parsed YAML key positions.

## Remaining SDK/target gate — BLOCKED

The host report always says that driver FI (bus-off/error-passive), target
overrun flood, real restart chain, target RX/TX byte-exact (three consecutive
runs each direction), and live QNX acceptance remain unproven. A passing CP103
fixture is **not** an overrun flood test; a passing CP102 fixture is **not** an
SLM restart test. Do not present host aggregate success as completion of target
C11. No shim, crash, overrun or target timing is fabricated by this library.
