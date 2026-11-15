# Diagnosis and single retry — 15 November 2026c

The prior continuous25fps attempt remains FAIL:100 host input frames,62 guest rows. Its originals/statuses are unchanged.

## Headless original-build diagnostic

One headless run, no X11 capture, used unchanged November8 recorder ELF725eb876fc700f72a62d8ba0344a7b30f3c0182d2036dfd361ed5e596918d513 and prereq ELF787039ffedf1e57879ee37516a19cb8a19548d5c1e0facdc26b9e02febb971bf. IFS764e7e9f3ffcb74e851dce896a513c85abe16589d918937f3ba5157891882a22; disk59269af3ae940d2e520271e8b2e989cc8de5918c8e6cf283bc88cfd734c30951, snapshot=on. Source hashes remain original frozen prep, not current-tip acceptance.

Result:100/100 ordered byte-exact RX and100/100 ordered byte-exact TX PASS, after SLM replacement286738→339986. Original30ms host cangen gap retained. Original guest recorder was not changed. CPU100000/100000,nice15,HOST2GiB,swap0,guest512MiB/1vCPU,TCG256MiB,reserve64MiB. Own QEMU809756 reaped; lease checked free immediately afterward.

This is consistent with capture contention but does NOT establish causation: not a controlled repeated experiment. No product bug demonstrated. Conservative single screen retry uses5fps instead of25fps and explicit100ms host cangen gap instead of30ms; this is a paced functional check, not throughput or latency evidence. Guest TX helper unchanged. Capture-only helper suppresses screen output and readability pauses only for diagnostic. No product source changes,SDK build,activation or install.

## Private bindings

Private root: workspace .openclaw/tmp/can-recording-20261115c. Diagnostic headless/receipt.json SHA256: 8b131c88cae075dcfde586a38c1cd95636350634963e2151d85d1ac60e94fa3d. Diagnostic serial SHA256: 44078a50504e63fe803fa5538dfcfbfe89d7d77497a3cf96466077856dda35aa. Capture helper differences preserved there. Host-only tests exercise valid100,missing38,reversal,changed payload rejection; actual empty browser/X11 proof and full adapter/browser contract preflight precede the one capture run. No previous logs/footage may substitute for that capture.

## Retry

Exactly one continuous actualX11 attempt is authorized. Final status appended after execution; existing private draft446240848 asset751796962 is untouched pending parent independent review. No safety,timing,availability,SocketCAN target,C6/controller/heartbeat claims.
