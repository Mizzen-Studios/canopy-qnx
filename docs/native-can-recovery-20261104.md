# Native CAN recovery — 4 November 2026

Private internal target evidence; not a public QNX evaluation.

## Fault narrowed and corrected experimentally

The QNX Intel legacy PCI module attaches dev-can-linux's INTx event to IRQ10 (pidin irqs: 0xa). SeaBIOS/QEMU's PIIX routing register at PCI 00:01.0 offset0x60 reads 0x0b0b0a0a; Kvaser at slot4 has configuration IRQ11. Before correction, 100 host frames produce zero RX rows and one TX completion. SJA1000 is in normal Pelican mode (MOD=0, CDR=0xc7), interrupts enabled (IER=0x7f); receive status becomes0x2f (pending/overrun) and S5920 INTCSR becomes0x802000. This is not an ACK/mode-only failure: IRQ handling is not draining hardware.

An explicit qtest experiment routes PIRQ A-D to IRQ10 by writing0x0a0a0a0a at PIIX PCI offset0x60. Board IRQ then clears and receive status returns0x2c. No driver source patch or GPL code was copied into this repository.

First routed run: 100/100 TX byte-exact, 96/100 RX at10ms host spacing. Do not hide that loss. A second run adds300ms settling after routing and30ms host spacing: **100/100 native RX rows and100/100 native TX frames**, both ID/DLC/payload exact. The checked-in harness independently repeated the100/100 gate and exits nonzero unless all counts, payloads and completion marker agree. This is a paced correctness test, not throughput/losslessness/restart qualification. Identical frame payloads do not establish sequence uniqueness.

## Reproduction boundary

Use tools/qnx_can_gate.py via scripts/qemu-capped.sh with an external image directory, output label and end marker QNX_TRAFFIC_GATE_END. Requires external licensed ifs.bin/disk-qemu containing the separately obtained dev-can-linux1.12/candump/cansend and the existing native traffic startup. Host vcan1 must be up. No guest binaries, GPL implementation, SDK or image included. The harness explicitly changes emulated PIRQ routing; it is NOT evidence of a corrected production BSP configuration. Resolve QNX pci_hw routing configuration and remove qtest dependency before calling the target deployment ready. vcan0 was not used or changed.

The original mods-can.so ABI gate remains unresolved. Reliable paced fallback traffic is now demonstrated; application/libcan integration and robustness acceptance remain.

SSH config-only diagnostic with OPENSSL_ia32cap=0 exits0 while the default environment exits139; full SSH daemon/connection proof remains separate. Native EDU has compiled but its first runtime attempt crashed; see edu-kit follow-up evidence.
