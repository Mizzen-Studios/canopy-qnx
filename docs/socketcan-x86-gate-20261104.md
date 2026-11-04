# QNX x86 CAN source gate — 2026-11-04

## Scope and conclusion
Read /home/ubuntu/briefs/qnx/plan_v3.md (SHA256 2e03816c5a6378764d658e744ff356df57f1126b6f32fa88efe5be5a118e7622). Public-source inspection only. No login, credential access, SDK install, accounts, spend, contact, publication, application-repository changes, or target execution. All artifacts remain under this source/ directory. Active licence alone does not prove an installed SDK/guest.

**Availability gate passes for x86_64 mods-can.so, not for an x86_64 board binary or live loading.** No supplied devs-can-vcan.so exists, on either architecture. No upstream Kvaser/SJA1000 io-sock board exists. ELF identity is not runtime/ABI compatibility proof. Additional concern: supplied module has unresolved sockcan_protosw; capture actual guest loader diagnostics before committing to the primary path.

## Immutable source identities
- https://github.com/qnx/socketcan current HEAD observed = requested known pin = 9db62b4747d84135a500dbfe3a318a4330f31654; tree 3592e45b0d33ae32baf8a4fb8af3b795dc31e7cd. Thus no current-vs-known code delta.
- x86 module Git blob b3f0a748aedb981e9a20df9443917c4463b1dda5.
- https://github.com/Deniz-Eren/dev-can-linux HEAD and release v1.12.0 commit f120bdb001e289b3335bdefe37acab945fabcd99; tree 17f5c5ef111e21d676f8208a69da5543cd206641.
- Its workspace submodule is pinned d71f233ffffec0db977fcbf0ba650e61de6e777b and was not initialized. Default CMake build needs that external workspace/toolchain support.

## Supplied binary inventory (paths relative to source/)
| Path | Actual file/readelf identity | SHA256 |
|---|---|---|
| socketcan/lib/can/nto/x86_64/dll/mods-can.so | ELF64 LSB DYN x86-64, not stripped, debug_info; BuildID ad524e204092fbadf436fb6caea72b71 | 45cb8b57889b0827b70385692c44ba76d8d49b618e6ae009ee37d0e3e11adea2 |
| socketcan/lib/can/nto/aarch64/dll.le/mods-can.so | ELF64 LSB DYN AArch64, not stripped; BuildID dce67a331d1cc077e4e9d24ec5f443a5 | 55ce79850c604f086ee5e77f3c98d576a122cfe207b2e13952e3007a852ad158 |
| devs-can-vcan.so | ABSENT from tracked repository; source only at socketcan/boards/can-vcan/ | n/a |

Module dependencies include libc.so.6 and libgcc_s.so.1. x86 strings identify QNX8 GCC 12.2.0 and QNXOS_805 build paths; not a guarantee of compatibility with a particular SDP/io-sock image. Dynamic exports include sockcan_alloc/register/fini/input/output/domain_create; undefined symbols include stk_ctl, domain_add/remove and sockcan_protosw. The latter requires a matching loader environment; do not assume a stand-alone module resolves it.

## README commands: documentary verification, NOT executed
README.md lines 54–89 actually gives full paths, spaces after -m and -d, and .so extensions:

	source target command (not a host command):
	io-sock -m /data/home/qnxuser/mods-can.so -d /data/home/qnxuser/devs-can-vcan.so -o prefix=/can
	SOCK=/can ifconfig
	SOCK=/can ifconfig vcan0 create
	SOCK=/can ifconfig vcan0 up

boards/can-vcan/README.md also documents 'SOCK=/can ifconfig vcan4 create up'. Therefore requested shorthand 'io-sock -m mods-can.so -d devs-can-vcan.so -o prefix=/can' matches the documented option structure, but bare-name search paths are NOT established here: prefer absolute deployed paths. The spelling '-ddevs-can-vcan.so' is not the README's exact form. Loading alone does not create an interface. Prefix clients with SOCK=/can to avoid the main network stack. Root README mount example does not establish mounting into the prefixed instance; do not extrapolate it.

## Builds and board API
Root README lines 31–43: host cross-compilation only; 'make' builds drivers, but the module cannot currently be rebuilt because internal io-sock hooks remain missing. Remaining source is reference-only. lib/can/Makefile.dnm is not the standard Makefile and is empty; this does not make internal sources available. Public sockcan_domain.h explicitly references remaining internal dependencies. Do not claim obtaining SDP alone fixes module rebuild.

All four board subtrees have nto/aarch64/dll.le only: can-vcan, can-dummy, can-libcan, can-mcp25xxfd. No boards/**/nto/x86_64, no tracked driver .so. samples can-read/write do include x86_64 build directories. Board common.mk includes qconfig.mk, devs/devs.mk and ../../lib/can/public; module includes devs/mods.mk. Required environment: licensed QNX SDP target x86_64 compiler, QCONFIG/recurse make infrastructure, io-sock DDK headers/build fragments and matching runtime ABI. Host native gcc is not a replacement. Add x86_64 build variants in a separate authorized work area when SDK available; not done in this task.

Public driver interface: socketcan/lib/can/public/hw/libsockcan.h (Apache notice) requires sockcan_dev_t as FIRST member of custom softc. Exact signatures:

	sockcan_dev_t *sockcan_alloc(const char *name, struct ifc_data *ifd, size_t softc_size);
	int sockcan_register(sockcan_dev_t *dev);
	int sockcan_fini(sockcan_dev_t *dev);
	int sockcan_input(struct can_pcb *pcb, sockcan_dev_t *dev, struct mbuf *m);
	int sockcan_output(sockcan_dev_t *dev, struct mbuf *m, can_tag_data_t *tag);

bittiming/data_bittiming callbacks: int (*)(struct sockcan_dev_s *dev, can_bittiming_t *bt, bool set). sockcan_dev_t also holds ifp, caps/enabled_caps, nominal_bt/data_bt, mutex and connected socket list. Output delivers received frames to sockets and takes mbuf ownership; input sends client frames toward hardware and also takes ownership. Timestamp in m_pkthdr.rcv_tstmp with M_TSTMP, not tag. tag flags include loopback and FD; MTAG_CAN=1128481584, MTAG_CAN_INFO=0. These signatures describe current public headers; ELF symbol names alone cannot prove signature/layout parity.

Apache-noticed dummy implementation sets if_transmit(struct ifnet *, struct mbuf *) -> int, if_qflush(struct ifnet *) -> void, if_ioctl(struct ifnet *, u_long, caddr_t) -> int. Lifecycle int candummy_attach(void), void candummy_detach(void); module glue uses DECLARE_MODULE, MODULE_DEPEND(candummy,can,1,1,1), MODULE_VERSION and IOSOCK_MODULE_VER_SYM_INIT. Virtual board uses int vcan_attach(void)/void vcan_detach(void), if_clone and analogous module glue. New real PCI board still needs PCI attach/BAR handling, SJA1000 RX/TX/interrupt/error paths and restart-safe teardown; dummy/vcan do not supply those.

can-libcan is a proxy over an existing /dev/canX libcan driver, not a Kvaser driver. Its README says only tested with can-mcp2515; single-consumer mailbox requirement; bit timing ignored in proxy. This gives a possible fallback bridge, not tested compatibility with dev-can-linux.

## Licence provenance: do not label entire import Apache
- Root socketcan/LICENSE.md is Apache-2.0. Public hw/libsockcan.h, hw/socketcan.h, sockcan.c and dummy.c/dummy.h/dummy_module.c explicitly carry BlackBerry 2026 Apache-2.0 notices.
- BUT boards/can-vcan/vcan.c, vcan.h and vcan_module.c each explicitly state BlackBerry retains proprietary rights and any use/reproduction/disclosure/distribution without an express licence agreement is strictly prohibited. Public visibility/root licence does not erase this conflict. Do not copy/relicense vcan into Apache projects or publish its build absent resolved permission. The active SDP licence has NOT been checked against these exact files.
- Supplied mods-can.so contains internal/reference-source-dependent code and no independently verified binary-specific grant was established. Root Apache and Experimental/QDL notices are evidence, not blanket clearance for closed-source hooks or binary redistribution. Fetch externally pinned; preserve provenance; distribution remains a separate owner/licence gate.
- dev-can-linux package ships GNU GPL v2 LICENSE matching repo LICENSE byte-for-byte. Its Linux-derived src/kernel/drivers/net/can/sja1000/kvaser_pci.c explicitly SPDX GPL-2.0-only; credits Per Dalen, Deniz Eren, Kvaser, Lincan, SocketCAN/SJA1000 and Volkswagen contributors. Some wrapper/build files state GPL v2-or-later; do NOT simplify every file to or-later. No GPL source copying into an Apache-labelled driver. Keep executable separate and satisfy applicable source/notice obligations before any distribution; legal compatibility not decided here.

## Public fallback package actually inspected
Public GitHub latest release observed: v1.12.0 (not immutable), https://github.com/Deniz-Eren/dev-can-linux/releases/tag/v1.12.0 . Saved manifest fallback-release.json. Downloaded only third-party driver package, not SDP:
https://github.com/Deniz-Eren/dev-can-linux/releases/download/v1.12.0/dev-can-linux-6.18-1.12.0-qnx800-x86_64.tar.gz
SHA256 fcfa5b656ee59ac16f917c93dd9ecc95d420a8903b9c2fc0e520856bce644c2f matches GitHub asset digest.

Exact archive members: bin/candump, bin/canread, bin/cansend, bin/dev-can-linux, share/dev-can-linux/LICENSE, share/dev-can-linux/README.md (plus directories). Extraction under fallback-qnx800-x86_64 only. Each bin/* is ELF64 LSB x86-64 PIE, dynamically linked, /usr/lib/ldqnx-64.so.2, debug_info, not stripped.
Driver SHA256 528580ccf32a2b41a896e27a928e956adea0b09dc1409e3062d2d41160ef96c1. Other binary hashes and all readelf headers/dependencies in elf-evidence.txt.
This is a monolithic dev-can-linux executable containing kvaser_pci support, not devs-can-sja1000.so and not a per-Kvaser .so. Repo README lines 593–597 explicitly lists Kvaser 10e8:8406 (QEMU model ID), source kvaser_pci.c exists, binary strings include kvaser_pci and GPL notices. No runtime -i/-ii command was executed. Packaging and strings are not proof of hardware operation. Its candump/cansend are libcan-oriented tools; do not confuse them with SocketCAN can-utils of the same basename.
Fallback source build needs CMake >=3.22, C/C++17, QNX compiler/headers and PCI library, and pinned workspace submodule/toolchain; CMake defaults to qnx800-x86_64 when QNX_HOST is set. No build performed.

## Decision table: execute only after SDK/guest is available and authorized
| Gate | Next action | Decision |
|---|---|---|
| Licence/notices | Resolve vcan source-specific permission and module use/distribution scope locally against applicable terms | Do not treat root Apache as blanket clearance; use independently Apache-noticed dummy as implementation reference |
| x86 module load | Deploy pinned external module to guest-only staging; capture io-sock version, loader stderr/slog2 and unresolved symbols | Success advances to board build; failure on internal ABI/sockcan_protosw blocks primary path; no host ELF test substitutes |
| Board build | Build an x86 variant with matching io-sock DDK; verify output file/readelf; do not attempt impossible public-only module rebuild | Virtual smoke test only after licence clearance; then independently implemented PCI/SJA board |
| Dedicated stack | Run exact absolute-path README command; record both stack PIDs, SOCK=/can interface create/up and module versions | Proves prefix semantics only when actual target succeeds |
| Real CAN | QEMU kvaser_pci + host SocketCAN backend; verify guest 10e8:8406; test byte-exact RX/TX repeatedly and IRQ/error teardown | No upstream real Kvaser io-sock board: our driver is required for direct primary path |
| Fallback | In guest run separate GPL driver -V/-i/-ii; verify detected Kvaser, /dev/canX, libcan RX/TX | If works, choose explicit native-libcan adapter, or separately test can-libcan bridge; no silent SocketCAN claims |
| No usable physical path | Licensed/cleared on-target virtual route | Label virtual-only; not QEMU hardware/IRQ validation |
| Restart/isolation | Kill only dedicated stack PID; verify main PID/SSH and fresh frames | Only then claim live load/restart/isolation; nothing here was load-tested |

## Reproduce actual inspections (safe, non-executing ELF tools)
From this source directory:

	git -C socketcan rev-parse HEAD HEAD^{tree}
	git -C socketcan ls-tree 9db62b4747d84135a500dbfe3a318a4330f31654 lib/can/nto/x86_64/dll/mods-can.so
	file socketcan/lib/can/nto/x86_64/dll/mods-can.so
	readelf -h socketcan/lib/can/nto/x86_64/dll/mods-can.so
	readelf -d socketcan/lib/can/nto/x86_64/dll/mods-can.so
	readelf --dyn-syms -W socketcan/lib/can/nto/x86_64/dll/mods-can.so
	sha256sum socketcan/lib/can/nto/*/*/mods-can.so
	tar -tzf dev-can-linux-6.18-1.12.0-qnx800-x86_64.tar.gz
	file fallback-qnx800-x86_64/bin/*
	readelf -h fallback-qnx800-x86_64/bin/dev-can-linux
	readelf -l fallback-qnx800-x86_64/bin/dev-can-linux
	readelf -d fallback-qnx800-x86_64/bin/dev-can-linux
	sha256sum dev-can-linux-6.18-1.12.0-qnx800-x86_64.tar.gz fallback-qnx800-x86_64/bin/*

Do not use ldd or execute untrusted target binaries on host. elf-evidence.txt contains actual command output, not inferred architecture from path names.
