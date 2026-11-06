# Bounded SocketCAN application (private experimental checkpoint)

Original source: native/socketcan_demo.c. This is an application, NOT an io-sock board driver.
No SDK, headers, binary or third-party implementation is distributed here.

## Build outside the checkout

Linux (real SocketCAN, not a mock):

	src="$PWD"
	mkdir -p "$HOME/canopy-build"
	cc -std=c11 -O2 -Wall -Wextra -Werror "$src/native/socketcan_demo.c" -o "$HOME/canopy-build/socketcan_demo"
	CANOPY_DEMO_BINARY="$HOME/canopy-build/socketcan_demo" python3 -m unittest discover -s tests -p test_socketcan_demo.py -v

For an explicitly dedicated, already-created Linux vcan interface, also set CANOPY_DEMO_VCAN=vcan1. Do not share it with another traffic gate/session. The live test verifies 100 byte-exact RX, 100 independently observed TX, and rejection of a wrong RX payload.

QNX SDP 8.0 cross-build, in an authorized SDK environment:

	source /path/to/qnx800/qnxsdp-env.sh
	qcc -Vgcc_ntox86_64 -g -Wall -Wextra -Werror -I"$SOCKETCAN_SOURCE/lib/can/public" "$src/native/socketcan_demo.c" -o "$HOME/canopy-build/socketcan_demo-qnx" -lsocket

SOCKETCAN_SOURCE is an external pinned qnx/socketcan checkout (9db62b4747d84135a500dbfe3a318a4330f31654); only its public hw/socketcan.h API is included. Keep all external headers and resulting binaries OUTSIDE this repository. Do not copy proprietary samples/boards into this project. Use matching installed io-sock headers where required.

## Run contract (target runtime NOT yet accepted)

A working, separately verified SocketCAN stack and interface are prerequisites. Do not replace the main io-sock stack or alter SSH/authentication settings to run this demo.

	SOCK=/can /external/path/socketcan_demo-qnx rx vcan0 100
	SOCK=/can /external/path/socketcan_demo-qnx tx vcan0 100

The actual interface name must come from the dedicated stack's ifconfig output, not from /dev/can0. The existing native libcan fallback uses device files; it is NOT SocketCAN and cannot run this application. A failing module ABI/board gate remains a blocker, not permission to substitute libcan results.

- RX: standard data ID 0x123, exactly eight bytes 01 02 03 04 05 06 07 08. A matching-ID wrong payload fails immediately. Extended/RTR/error frames are excluded.
- TX: standard data ID 0x321, exactly eight bytes 11 22 33 44 55 66 77 88, paced 30ms. TX_ACCEPTED counts successful writes only; an independent peer must establish delivery.
- Count bounded 1..1000; nonblocking socket, poll and monotonic deadline (10 seconds plus 30ms per requested frame). Full count or nonzero failure; no silent partial success. Classic CAN only, no FD.

Keep target and host counts separate. The 6 November native QEMU 100/100 RX/TX evidence belongs to the libcan fallback driver, NOT this new SocketCAN application.
