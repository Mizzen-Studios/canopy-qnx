# Offline host replay evidence

2026-11-03 UTC. Host-only; no QNX or live CAN acceptance implied.

* docs/replay/run.jsonl: 601 genuine Python host-model output records from
  ./canopy demo --script hero --seed 7 --host-sim. Tests compare all rows with
  the director and the exact embedded dashboard data. Byte-identical repeat.
* 41 standard-library unittest cases pass, including three new director tests
  and the page's actual JavaScript parser executed in Node. Invalid provenance,
  CRC, types, ranges, order, JSON and oversize inputs are rejected. CLI tests
  cover record, validate, self-contained export, top and overwrite refusal.
* Installed Playwright + Chromium 1243 (arm64), direct file://, no server:
  browser suite covers initial rendering, keyboard stepping/Home/End/Space/I,
  play/pause, speed selection, scrubbing, event jumps, real file input,
  invalid-file retention, sample reset and desktop/mobile width checks.
  No JavaScript errors or HTTP requests observed. 1920×1080 desktop also checks
  vertical fit. 390×844 mobile is intentionally scrollable.
* Screenshots are generated to REPLAY_EVIDENCE_DIR outside the repository:
  host-hero-1920.png and host-hero-mobile.png. Binary screenshots cannot be
  committed under the existing binary-free SDK guard. Tests require an explicit
  evidence directory to avoid leaving rejected binary artifacts in the tree.
* scripts/check-no-sdk.sh and git diff --check pass.

Reproduce browser verification without downloading dependencies:

    REPLAY_EVIDENCE_DIR=<workspace-scratch-outside-repo> \
    NODE_PATH=<existing-node-modules> \
    CHROMIUM_PATH=<existing-chromium-executable> \
    node tests/test_replay_browser.cjs

Earlier snap Chromium confinement limitations were bypassed using the already
installed native Playwright Chromium. No installation, public listener or Pages
publication was necessary. No ttyd shell, PIDs, restart timings, QNX QPP signals,
SSH drops or target performance are fabricated. See workflow.md for genuine
SDK/target blockers; non-SDK playback does not satisfy full C9/C10 acceptance.
