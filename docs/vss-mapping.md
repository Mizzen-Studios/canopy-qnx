# Project-owned CAN → VSS mapping v1

Scope: C5's SDK-independent portion only. These are **host simulation** values,
not OEM signals, vehicle measurements, QNX results, or a working QPP connector.
All files here are project-owned Apache-2.0; upstream QPP is not vendored.

| CAN ID | DLC | DBC layout | Physical value | VSS path |
|---|---|---|---|---|
| 0x100 | 2 | 0|16@1+ (Intel unsigned) | raw × 0.01 km/h; 0..250 | Vehicle.Speed |
| 0x101 | 2 | 7|16@0- (Motorola signed) | signed raw degrees; -720..720 | Vehicle.Chassis.SteeringWheel.Angle |
| 0x102 | 2 | 7|16@0+ (Motorola unsigned) | raw × 0.01 m; 0..500 | Vehicle.ADAS.ObstacleDetection.Front.Distance |

Motorola start bit 7 is the MSB of byte zero; the next eight bits are byte one.
Steering is two's complement, positive left/negative right, integer degrees
because the pinned QPP catalogue uses int16. Speed is **km/h**, not the m/s
used by some existing host simulation internals: any eventual integration must
convert explicitly at that caller boundary, not reinterpret the same number.
No existing safety/runtime/replay code has been wired to this new module.
IDs 0x100..0x102 are project demo assignments, distinct from heartbeat 0x200.

No rounding/clamping; values must be on the exact wire grid. Raw values outside
the listed physical ranges are invalid (including all-ones); there is no
reserved no-obstacle sentinel. Missing/invalid/unknown input produces no sink
update, not zero or an invented far-away obstacle. No CRC/authentication is
added by this sensor mapping. Bus CRC alone is not an E2E safety mechanism.
Classic standard data frames only, no RTR/error/extended/FD. The two-argument
bare codec assumes the caller has already separated classic vs FD; the host
adapter has an explicit is_fd guard. SocketCAN parsers must preserve flags
until validation rather than mask them away.

## Host use (no service writes)

```python
from canopy_host.vss import HostAdapter, SPEED, encode, qpp_text_write
updates = []
adapter = HostAdapter(updates.append)
ident, payload = encode(SPEED, 12.34)
update = adapter.receive(ident, payload, source="host simulation example",
                         received_ns=1000)
intent = qpp_text_write(update)
assert payload.hex() == "d204"
assert intent.filename == "/dev/signal/Vehicle/Speed?text"
assert intent.payload == b"12.34\0"
# intent/update retain source metadata; no files were opened or published.
```

## Host verification observed 2026-11-03

Commands from isolated branch work/core-vss-20261103:

- `python3 -m unittest discover -s tests -p test_vss.py -v`: **13 pass**.
- `python3 -m unittest discover -s tests -v`: **51 pass** (38 existing + 13).
- 12 hand-calculated golden vectors in `vss/golden.json`, each source-labelled
  host simulation. Fixtures cover zero, resolution, non-palindromic endian,
  signed negative values and physical limits.
- Exhaustive test traverses **196,608 raw inputs** (65,536 × three signals),
  checking exact valid encode/decode or invalid-range rejection. This is host
  codec correctness evidence, not timing/performance or QNX evaluation.
- Tests guard DBC/header/scale/endian/range consistency, overlay declaration,
  malformed input/flags/types/DLC, precision-independent scaling, FD rejection,
  source/time validation, sink failure and POSIX text write-intent formatting.
- `sh scripts/check-no-sdk.sh` and `git diff --check` pass.
- External DBC validator `cantools` is **not installed**; none downloaded.
  Regex contract tests are not claimed as an independent DBC parser validation.
- No VSS exporter is used; overlay merge/export and catalogue loading remain
  target/tooling acceptance gates. No QNX compiler `qcc` is present.

See [pinned API evidence and target integration gates](vss-qpp-integration.md).
