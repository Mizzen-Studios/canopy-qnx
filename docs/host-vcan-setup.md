# Host SocketCAN setup — 2026-11-03

Installed can-utils2023.03-1 from Ubuntu apt. Loaded existing vcan module and created vcan0 UP, without changing persistent network/service configuration. Existing host interfaces were preserved. Package status installed; dpkg audit clean.

Reproduce on Ubuntu host:

```sh
sudo apt-get install --no-install-recommends can-utils
sudo ./scripts/setup-vcan.sh vcan0
```

The script only creates/raises an explicitly selected vcanN and refuses an existing non-vcan interface. It does not add boot persistence. To remove an unused dedicated interface, explicitly run `sudo ip link delete vcan0`; do not do this while the host runtime is using it.

## Actual host-only evidence

Three bounded runs of `cangen vcan0 -g 1 -n 100 -I i -L 8 -D i` were collected by a Linux raw CAN socket. Each received exactly100frames: IDs0..99, DLC8, payload equal to index encoded as8byte little-endian. All300byte comparisons passed. This is HOST VCAN evidence, not QNX, kvaser driver, electrical bus, interrupt or overrun acceptance.

Local full captures/results: `.openclaw/tmp/qnx-core-20261103/host/vcan-run{1,2,3}.json` and `vcan-results.json` in the workspace outside the repo.

Demo of fail-safe patterns; not an ISO 26262 / IEC 61508 claim.
