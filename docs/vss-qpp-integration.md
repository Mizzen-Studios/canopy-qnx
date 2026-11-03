# CANopy VSS / QPP boundary — host implementation, target blocked

Status: SDK-independent mapping implemented and host-tested. **No QNX build,
QPP service execution, live CAN or QPP publication has been performed.**
This does not close the on-target part of C5. No upstream source is vendored.

## Pinned read-only source research (2026-11-03)

Repository: https://github.com/qnx/qnx-posix-publish-subscribe
Commit: **b5ca892f37464bea4ff88db3fdbbb2cc651da6a8** (resolved using

guarded read-only `gh api repos/qnx/qnx-posix-publish-subscribe/commits/HEAD`).
All following paths refer to that commit, not floating master:

- `signal-framework/README.md`: connectors are source-facing processes;
  Signal Service is a QPP POSIX resource manager. There is no evidence here
  of a shared-library plugin registration interface; do not invent one.
- `qpp/README.md`: QPP uses open/read/write/poll; a custom mount is set
  with --mount/-m, and --catalog/-c loads a JSON tree. Text interface accepts
  a NUL or newline terminator and a `?text` modifier.
  Catalog creation is documented against **VSS version 3.0** tooling.
  min/max/unit metadata are **not enforced by QPP**; the connector must validate.
- `playback/playback-connector/signal_writer.c`:
  `signal_writer_send` parses path/value; `signal_writer_cache_path`
  replaces VSS dots with slashes and opens `<mount>/<path>?text` O_WRONLY;
  `signal_writer_write_text` writes the scalar text plus its NUL terminator.
  Binary writing returns ENOSYS in this implementation.
- `playback/playback-connector/connector.c`:
  `pb_connector_create/start/stop/destroy` are local lifecycle functions,
  not a public plugin ABI. The example reads playback socket events and
  invokes its signal writer, with a control pipe to stop the poll thread.
- `signal-framework/connectors/echo-actuator/connector.c`:
  `get_control_path` maps actuator requests to a hidden leaf
  `.<name>.control`. Sensors in this work are **not** actuator requests;
  encoding sensor values for fixtures does not authorize reverse actuation.
- `playback/playback-connector/common.mk`: QNX qconfig.mk/qtargets.mk,
  QNX_TARGET, MKFILES_ROOT, upstream libqpp/libplayback headers/library
  paths, libraries json/socket/slog2/qpp/playback. x86_64 target directories
  exist, but their existence is not evidence of a working build here.

The pinned sample catalogue at
`signal-framework/signal-service/etc/signal_catalog.json` (Git blob
`34fb936afe8b7dc07d4d483bffa1552c0f2a9ea7`) starts with a C comment saying
it is based on VSS 3.0 plus extensions. Read via GitHub contents API base64,
remove the leading C comment for JSON inspection (it is not plain strict JSON).
Directly inspected nodes:

| Signal | Catalogue type / unit | Decision |
|---|---|---|
| Vehicle.Speed | float / km/h | No m/s-to-km/h ambiguity at this boundary |
| Vehicle.Chassis.SteeringWheel.Angle | int16 / degrees; positive left | Integer-degree wire resolution; no silent fractional truncation |
| Vehicle.ADAS.ObstacleDetection | Branch with IsEnabled/IsError/IsWarning/Lane | Front.Distance absent; merge our overlay |

The installed target catalogue remains uninspected (no SDK/image). Do not
assume it equals the repository sample. If higher-resolution steering is
required, explicitly revise/version the catalogue and mapping together rather
than write fractional text to an int16 signal.

## Implemented host boundary

`canopy_host/vss.py` is stdlib-only and fixed to the project-owned DBC;
it is deliberately **not a general DBC parser**. `encode(path, value)` rejects
rounding, nonfinite values and range violations. `decode(can_id, bytes)`
rejects unknown IDs, all SocketCAN EFF/RTR/ERR flags, wrong lengths and types,
and out-of-domain raw values. `HostAdapter.receive(..., source=...,
received_ns=..., is_fd=False)` validates before calling an injected sink.
CAN FD is rejected even if its data happens to be two bytes long.

Each immutable Update contains path/value/unit/**source**/received_ns. Use
`host simulation fixture` for fixtures; never label these as QNX values.
Clock is caller-supplied monotonic reception time, not wall clock, remote
clock or proof of freshness. Ordering/stale detection belongs to the runtime,
not this stateless mapping. Source tags are labels, not authentication.
Sink errors propagate and do not count as successful publications.

`qpp_text_write(update, mount)` produces a checked **write intent only**:
allowlisted filename, scalar ASCII plus NUL, and the original source-tagged
Update. It never opens files, starts a service or publishes anything. A host
sink can collect these for tests; no host ordinary-file write is represented
as QPP success. Provenance travels in the Update sidecar, not appended to
numeric QPP payloads. A future telemetry path must retain that sidecar.

## Target integration design / exact remaining dependencies

1. Owner supplies licensed QNX SDP 8.0 toolchain and target image outside git,
   with QPP executable/service, x86_64 runtime libraries, and the actual
   SocketCAN/io-sock headers and module configuration. Confirm qcc target,
   QPP version, catalogue metadata and permissions. No SDK was downloaded.
2. Confirm permission/licence for using/building QPP: the inspected sources
   carry proprietary BlackBerry notices requiring an express licence.
   Public visibility does **not** make these Apache-2.0. This work copies no
   implementation, headers or SDK and does not infer redistribution rights.
3. Review the actual VSS3 base and merge `vss/canopy-overlay.vspec`;
   export JSON using the matching VSS tooling outside this host runtime.
   Verify metadata for all three paths (including steering int16) before
   accepting frames. Overlay merge/export is **not tool-validated here**.
4. Implement a standalone `canvss` target process: dedicated /can SocketCAN
   receive socket, filter IDs 0x100..0x102, strict classic frame/DLC checks,
   same codec semantics, bounded sink queue, stop/control wakeup, explicit
   connection status. Do not link a guessed QPP plugin ABI. Open existing
   value nodes O_WRONLY with ?text; never O_CREAT a substitute catalogue.
5. Check every complete scalar write (including short writes/EINTR/error),
   close invalidated descriptors on service restart, reconnect with backoff,
   and wait for a **new** valid CAN frame after reconnect. Do not refresh a
   stale value by re-publishing cached data. Invalid frames or service errors
   must not refresh freshness; retain source/timestamp outside QPP scalar.
6. Byte-exact target/host golden tests for all three signals; read back value
   nodes and metadata; reject malformed/FD/flagged/range-invalid inputs;
   test QPP restart, CAN-driver restart, missing node and write failure.
   Record compiler/runtime versions and actual transcripts before claiming C5.

No C connector skeleton is included: proprietary example-copying and an
unbuilt guessed ABI would add false confidence without the licensed target
headers/service. The real POSIX API and host adapter contract are specified
above; this is an integration design, not a compiled QPP plugin.

Fallback gate in plan v3 remains 25 November: if QPP cannot build, an explicit
/dev/vss resource-manager implementation may be chosen separately; it must
not be described as QPP. No fallback is silently enabled here.
