# Focused C6 scheduling attempt: FAIL

**observed in this QEMU run · app budget, not a QNX benchmark**

Fresh baseline:100RX and100TX ordered byte-exact. Native FIFO20 plus
CLOCK_MONOTONIC/MsgReceivePulse path unchanged. Hypothesis: remaining20r
CAN helpers starved behind FIFO20. Observed10r/20r helpers were raised24r
and independently inspected. Caps unchanged:CPU100%,1GiB,nice15;1vCPU/512MiB.

Result:850 native ticks/TX devctl returns versus one host0x200 heartbeat;
no healthy sensor samples. Hypothesis did not resolve failure. Root cause
remains undetermined in persistent libcan traffic; enqueue IPC success does
not prove CAN completion. No scenario accepted; C6 runtime UNVERIFIED.

Per owner stop rule, C6 lane is STOPPED after this focused attempt. Guest
stopped/reaped and lease released. Do not retry automatically. Next approved
lane:E2 host/docs polish only, not per-snapshot runtime acceptance.

experimental-profile.xml preserves the tested input, not a production config.
No safety thresholds, FIFO priority or timer interval were weakened.
