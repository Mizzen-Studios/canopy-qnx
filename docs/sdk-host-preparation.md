# SDK host preparation — private evidence, 2026-11-04

Owner reports an active perpetual non-commercial single-user SDP8 licence on this VM. Account/serial/credential values are not recorded here. Activation and entitlement have NOT been independently verified. Password file is absent; no login, licence-listing, activation or SDK installation has been attempted.

## Route decision

Existing Docker29.1.3 is available through sudo. Built local image `qnx-sdp-host:ubuntu24-amd64` (image5fade3dd0e7a) on ARM64 using registered QEMU8.2.2 user/binfmt. Official Ubuntu24.04 base index digest:sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852. SDK and persistent home must stay outside repositories, e.g. /home/ubuntu/qnx-host/container-home, mode700. UID1001 matches this VM user; adapt deliberately on another host before any activation. No QNX files included in image/recipe.

Linux smoke compiled an actual amd64 glibc2.39 program with GCC13.3 and passed pthread/fork/wait/posix_spawn/dlopen plus four threaded Python subprocesses. Compile2.465s, execution0.168s **observed in this QEMU run on this VM**, Linux-only internal evidence, not QNX/qcc evaluation. HOWEVER package setup and the final readelf/grep pipeline emitted QEMUinternalSIGSEGV0x20. The pipeline exited nonzero; initial tee wrapper masked that exit. Mark complete smoke **FAILED / unreliable**, not green. Partial successes do not establish SDK/QSC reliability. Full-system Ubuntu TCG fallback is being tested separately; do not activate a single seat in a disposable or unreliable container.

Recipe: sdk-host/Dockerfile, smoke.c, smoke.sh. Build/run locally only:

```sh
sudo docker build --platform linux/amd64 -t qnx-sdp-host:ubuntu24-amd64 sdk-host
sudo docker run --rm --platform linux/amd64 --network none --cpus 2 --memory 2g -v "$PWD/sdk-host:/smoke:ro" qnx-sdp-host:ubuntu24-amd64 bash /smoke/smoke.sh
```

The container is a candidate experiment, not the selected licensed SDK host. Never execute the x86 SDK directly on native ARM or use box64.

## Credential and safe CLI gate

1. Wait for owner-created ~/.secrets/myqnx; check parent700/file600/ownership, not its value. Waiting is SDK-blocked; no polling/login retry loop or chat password request.
2. Official Linux QSC2.0.4 installer is authentication-gated: https://www.qnx.com/download/download/79441/qnx-setup-2.0.4-202501021438-linux.run redirects unauthenticated requests to login. Verify actual downloaded binary/length/vendorchecksum, never save loginHTML as an installer. Vendor published104701288bytes and MD5bca161a97ab3e14189cf8e7c8227fb7d (integrity, not modern authenticity proof).
3. Inspect install destination before the documented bare-word arguments `force-override disable-auto-start agree-to-license-terms DESTINATION`; do not blindly overwrite an install. Install/run as the same persistent ordinary user, not root. Prove actual QSC -version/-help in the chosen environment before authentication/activation. Exact bundled JVM/lib requirements are not yet inspected.
4. CLI official auth options are -myqnx.user/-myqnx.password. Documentation says direct password arguments are logged cleartext and recommends @options_file, one argument per line. No automatic MYQNX_PASSWORD/stdin password protocol was found. scripts/qsc-auth.sh reads the password into an environment variable only after permission checks, writes transient mode600 options under private mode700 directory outside repos, unsets the environment value before invoking QSC, and removes options on exit. Raw output remains in a private log, never chat/commits. Synthetic mock tests cover missing/mode/symlink/multiline/repository failures and argv/stdout leakage; actual QSC behaviour remains untested.
5. Once safe authentication is available, list/sync deployed keys privately. The documented add-and-activate flag is -addLicenseKey, NOT an assumed -activateLicenseKey. Avoid -activateAll and repeated/multiple-environment seat activation.
6. Inspect actual -help/catalogue for -mirrorBaseline qnx800 and the exact com.qnx.qnx800 baseline ID/version; the former is only an official example, not a formal option entry. -mirror, -destination before -installBaseline, -installPackage and -verifyInstallation are documented. Do not guess version/entitlement. Generic x86 BSP ID:com.qnx.qnx800.bsp.hw.x86_64; current advertised build is experimental, so review available versions first.
7. Source installed qnxsdp-env.sh and compile a minimal target hello with qcc -Vgcc_ntox86_64. Then build/boot the licensed QNX image and perform [top-risk CAN gate](socketcan-x86-gate-20261104.md). All these steps are pending.

CLI reference: https://www.qnx.com/developers/docs/qsc/com.qnx.doc.qsc.user_guide/topic/commandline_qsc.html

Unattended installer: https://www.qnx.com/developers/docs/qsc/com.qnx.doc.qsc.inst_larg_org/topic/create_headless_installation_linux_macos.html

BSP release notes: https://www.qnx.com/developers/docs/BSP8.0/com.qnx.doc.bsp.releasenotes/topic/rel_sdp80.bsp.x86_64.generic.html

QSC support for Ubuntu24x86_64 does not prove every SDP minor release supports that userland. Public visibility of upstream CAN/QPP code does not override per-file proprietary/GPL notices. No headers/libs/images/BSP/QSC/cache/licence files may enter either project repo, even while private. Run scripts/check-no-sdk.sh before every push.
