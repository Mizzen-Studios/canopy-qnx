# Vehicle signal timeline — host interpretation of recorded bytes

Open the [portable desk](downloads/canopy-incident-desk.html), leave the recorded example in Historical mode, then choose **Decode recorded frames**. Expand **Configure a signal mapping** to edit local JSON. This is a separate signal sample view, not another event/PID timeline. Default mapping is explicitly illustrative recorder-byte interpretation, not a vehicle measurement.

## Evidence boundary

The two authorized public packs contain recorder test-pattern bytes with **no documented OEM vehicle meaning**. Existing project-owned VSS/DBC simulation assignments are separate host simulation and are not applied to recordings. No native speed, RPM, steering, DBC or vehicle integration claim.

Only actual observed rows are decoded. Expected rows are used solely by existing bound-traffic checks. Each point retains exact frame, ordinal, event, artifact line and text SHA256. RX observed serial provenance and separately host-bound TX observed bytes retain existing distinctions. Source links open traffic events; adjacent raw artifacts appear in Evidence trail. No path is fetched/executed.

Canonical lists have **no per-frame aligned timestamps**. X is observed frame ordinal, zero-based separately within RX/TX, not milliseconds, wall time or recovery duration. Collector event offsets and native serial TS values are not merged into an invented common clock. No connecting lines/interpolation. CAN-ID gaps are not missing samples. Missing/invalid values and outside capture remain UNKNOWN, never zero or held-last-value. Finite list differences do not establish exact loss times or absent signal values.

## Mapping contract

API: require('./tools/incident_pack/signals').analyze(originalJsonText, mappingJsonText, {mode:'historical'}).

Revalidates original bytes with untouched shared validator, then existing raw-list/digest/citation/process/serial checks for both directions before any points. Strict is default; historical exempts expiry only. Corruption/missing evidence returns UNKNOWN, no signals. UI clears samples on import/reset/origin/mode changes, failure and strict expiry. No pack rewrite/reseal.

Schema canopy.signals/1, exactly schema and signals; one to eight signals, JSON at most8192 characters. Each signal has exactly:

- label, unit: nonempty text, at most80 characters; user declarations, not verified semantics.
- direction: RX/TX; id: numeric standard11-bit CAN ID0..2047.
- byteOffset: zero-based byte; byteLength:1..4, within eight bytes.
- endian: little/big; signed: boolean, two's complement when true.
- scale, offset, min, max: finite numbers, nonzero scale, ordered inclusive bounds.

Decode byte-aligned integer, apply sign, then value = raw × scale + offset. No rounding/clamping. Nonfinite arithmetic/outside bounds yields UNKNOWN per sample. Bit-level Intel/Motorola start-bit conventions, multiplexing, FD, extended frames and DBC import unsupported. Duplicate mapping fields follow JSON.parse last-field semantics; mapping is interpretation, never evidence/provenance.

Labels use textContent, controls keyboard reachable, SVG has source-cited table equivalent; source links activate by Enter. No external requests/fonts/dependencies/uploads. Build: python3 tools/build_portable_desk.py; --check verifies reproducibility. Native/core/validator/original packs/pins/failures and C6 STOPPED unchanged.

[25 November host acceptance](acceptance/vehicle-signals-20261125/RESULT.md). Recording HOLD until features plus after8 December and separate owner release; no capture or external-publication authority.
