# Capture a new bounded QNX incident

**15 November live run:** [accepted recording and evidence](acceptance/recording-20261115d/RESULT.md), with the [public narrated video](https://youtu.be/f0yBRgMJvfk). Frozen-guest SLM restart and exact100RX/100TX passed; the desk inspected the fresh pack. Demo in QEMU; not a safety or latency claim.

**Separate guest_query gate (10 November, still NOT_RUN):** guest_query ELF qcc build PASS; new native query/recorder/SSH journey NOT_RUN, no fresh same-pack native acceptance. Stock mkifs procnto relink OOM at unchanged caps; [measured blocker](acceptance/query-retry-20261110/NOTES.md). The new guest-query/slog2 viewer is host-tested only. Original Nov8 example and bindings unchanged; SSH UNVERIFIED. This guide does not turn compile-only guest_query evidence into native runtime acceptance.


This is an active collector, not the historical museum pack. It uses an existing
licensed QNX8 x86_64 SDP/BSP and libcan fallback image. No SDK installation,
licence activation, new credentials, server, upload, or target SocketCAN claim.

The [dated supervision note](../config/supervision/README.md) explains the historical, hash-pinned XML comment and the later observed SLM start/restart.

## Build inside your licensed SDK host

Set CAN_SDP_ENV to your trusted qnxsdp-env.sh, CAN_BUILD_FILE to your own working
SLM/libcan image buildfile, CAN_BSP_CWD to its working directory, CAN_OUT to a new
external build directory. The image must already contain slogger2, slog2info,
slm, slmctl, dev-can-linux, candump, cansend, and slm-can-fallback.xml, and emit
CANOPY_SLM_IMAGE_READY after startup. These are prerequisites, not shipped SDK
assets. Run:

    mkdir -p "$CAN_OUT"
    bash tools/build_native_recorder.sh > "$CAN_OUT/build.log" 2>&1

Retain original sources and source revision/dirty-content digest, exact invocation,
full build log and all source/ELF/buildfile/IFS/disk digests outside git. Do not
reuse an old receipt for a new build. Historical SDK construction notes mentioned
an existing approved 1GiB swap; that is not authorization to enable swap now.
The frozen 15 November recording used a 2GiB host cap and zero swap; it reused
the bound guest image, not this newer build route. Do not change caps or run SDK
and target together.

## Collect on your Linux QEMU host

Requires existing can-utils, QEMU kvaser_pci and your preconfigured isolated vcan
interface (host transport only). Use a single shared lease for SDK and target.
Stop/reap the SDK VM first. The following is the older collector recipe, not a
reproduction of the frozen 15 November recording. That recording observed
CPU100%, nice15, host2GiB, swap0, guest512MiB/1vCPU and TCG256MiB under its
separately bound capture wrapper; see its [result](acceptance/recording-20261115d/RESULT.md).
No cap/controller changes or new native work are authorized here.
The current collector source still checks effective host CPU <=100%, memory
<=1GiB and nice>=15; target stays 1vCPU/512MiB. A user-scope example:

    systemd-run --user --scope -p CPUQuota=100% -p MemoryMax=1G nice -n 15 \
      python3 tools/collect_native_incident.py --image "$CAN_OUT/incident.ifs" \
      --disk "$CAN_DISK" --out "$CAN_CAPTURE" --lock "$CAN_NATIVE_LOCK" \
      --interface "$CAN_INTERFACE"

Choose a nonexistent capture directory. The collector refuses ambiguous identities,
starts actual SLM, invokes the separate native recorder against dev-can-linux,
observes replacement, and compares 100 ordered RX and 100 ordered TX frames using
independent host capture. It additionally invokes the actual threaded negative
control and snapshots slog2. All failures/raw serial/traffic remain; no retries
rewrite a prior incident. The narrow QEMU Kvaser PIRQ routing adjustment is recorded;
not a hardware BSP portability result. No safety/heartbeat/actuation/C6 work.

## Adapt, validate, import the same file

Create lineage.json with source/binary/image/disk objects, each sha256 (underlying
source set or file digest) and text (receipt). Record hash computation, committed
source revision + dirty-content digest, build invocation and input/output hashes,
boot image/disk lineage and exact collector revision/hash/run binding. The adapter
checks image/disk against capture and embeds these text receipts, not licensed files.
This is cooperative provenance, not attestation.

    node tools/incident_pack/native.js "$CAN_CAPTURE" "$CAN_LINEAGE" > "$CAN_PACK"
    node tools/incident_pack/cli.js validate "$CAN_PACK"
    node tools/incident_pack/cli.js query "$CAN_PACK" recovery

Open web/incident-pack/index.html and choose that exact CAN_PACK. No separate UI
schema. Review evidence links and export. Missing traffic/control/generations
cannot become observed recovery/isolation. Serial native records must be complete
sequence0..4; waitpid ECHILD is explicit because SLM owns the driver child. Raw slog2
preserves native timestamps/PID/TID/codes. Event ordering is ordinal, not a latency
measurement. Traffic encoding is decimal ID + ':' + 16 lowercase hex bytes + newline,
preserving order; both complete streams are embedded and independently hashed.

No SSH continuity is emitted. Before/after io-sock snapshots are not uninterrupted
availability, adversarial isolation, platform health, security policy or safety.
Historical receipts are unchanged. Repeated runs create new IDs and new packs.
