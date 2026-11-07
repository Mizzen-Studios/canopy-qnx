# C6 native failure — 2026-11-07

**FAIL: native/host 0x200 heartbeat mismatch. Runtime gate UNVERIFIED.**

**observed in this QEMU run · app budget, not a QNX benchmark**

850 native timer ticks / TX devctl returns versus one independently captured heartbeat. All native states SAFE_STOP, fresh=0; sensor ages missing. IPC success is not proof of CAN transmission. Startup braking is not functional fault acceptance.

Receipt binds source/image hashes and CPU100%,1GiB,nice15; guest1vCPU/512MiB. Scheduler output records FIFO20. Experimental service/helper24r priorities did not resolve mismatch. Prior100RX/100TX baseline is not a fresh baseline in this run. Guest stopped/reaped. Libcan fallback only, NOT SocketCAN acceptance.

No stale/obstacle/kill/bad-CRC/frozen/N-fresh runtime scenario accepted. Next:one focused transport diagnosis, preserving thresholds and pulse/FIFO path. Experimental profile remains unaccepted, not production supervision.
