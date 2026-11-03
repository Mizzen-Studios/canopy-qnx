# Offline replay evidence

2026-11-03 UTC. The built-in JSONL is generated directly by
python3 -m canopy_host.sim --scenario drop --seed 7.
Tests compare every fixture row with the current model and verify that the
standalone HTML embeds exactly the same fixture. No fabricated measurements.

Node.js executes the page's actual parseReplay function against the full valid
fixture and rejects invalid source/type/range/order/JSON/size cases. Static
checks verify the explicit simulation labels and no network dependency.

Headless Chromium file:// attempt was denied by snap AppArmor filesystem
confinement (ERR_ACCESS_DENIED), so no direct local-file screenshot was produced.
A data-URL headless Chromium DOM check passed (exit 0), avoiding any server
or port: rendered initial speed 9.00, initial actuator watchdog stop and 351
asserted-watchdog timeline slices. This proves initial rendering, not interaction.
No screenshot or visual layout pass is claimed; 1920x1080 and responsive CSS
are implemented but visual review remains unverified. File-picker interaction,
playback controls and keyboard behavior have not had a browser interaction test.

No QNX, live CAN, vcan, SSH or physical vehicle evidence is implied.
