# Supervision reference — 15 November 2026

The opening “NOT yet validated” comment in [slm-can-fallback.xml](slm-can-fallback.xml) is historical. The [15 November live run](../../docs/acceptance/recording-20261115d/RESULT.md) starts SLM with this configuration and verifies the managed driver restart368658→421906 and100RX/100TX ordered byte-exact traffic. [Public narrated video](https://youtu.be/f0yBRgMJvfk).

The XML is byte-pinned by the historical recorded workbench manifest. Even a comment edit makes that verifier reject it as corrupt/mixed evidence. This dated companion note corrects the reading without rewriting historical hashes, receipts or verifier code; the XML bytes are deliberately unchanged.

This is scoped QEMU evidence, not production supervision-policy validation. Rolling-window/manual-latch enforcement still requires a policy controller. C6 FAIL / STOPPED; guest_query native NOT_RUN; SSH/SocketCAN UNVERIFIED. Demo in QEMU; not a safety or latency claim.
