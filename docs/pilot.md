# Learned pilot — HOST SIM only

This completes the SDK-independent portion of C7. It does not establish QNX
runtime inference, scheduling, QPP transport, or target veto behaviour.
The source is a synthetic host kinematic demonstration, not road data or captured
QNX telemetry. Existing safety and replay implementations are unchanged.

## Reproduce from repository root

Requires Python 3 standard library and a host C99 compiler named cc (no packages).

~~~sh
python3 -m ai.generate
python3 -m ai.train
python3 -m unittest discover -s tests -p test_pilot.py -v
python3 -m unittest discover -s tests -v
sh scripts/check-no-sdk.sh
git diff -- ai/sim_logs.jsonl ai/pilot_model.json ai/pilot_model.h ai/modelcard.md
~~~

Regeneration is deterministic: the last diff should be empty on the same source
revision. Training source and safety API SHA-256 hashes are embedded in the JSON.
If the safety source changes on integration, review the API and rerun training to
update provenance (the safety module supplies no training labels). The baseline
source revision is recorded separately; hashes identify exact inputs. This is
local host work; it downloads no SDK or datasets and invokes no external service.

## Data and learning

ai/generate.py allocates seeds 0–7 to training and 100–103 to held-out before
sampling any rows. Every scenario for a given seed follows that assignment.
There are three scenario families and 32 logical-time samples per trace: 768
training rows in 24 traces and 384 held-out rows in 12 traces. Held-out scenarios
are familiar families with unseen seeds/traces; this is not unseen-family testing.

A scripted demonstrator labels five joint speed/steering classes. This is explicitly
supervised imitation learning: the teacher is handwritten, the inference splits
are learned. ai/train.py searches integer midpoint thresholds by weighted Gini
impurity using exact rational scores, stable feature/threshold ties and lowest
class-ID majority ties. Only training rows enter fitting. Fixed limits: depth 5,
minimum leaf 4. There is no preprocessing, tuning or held-out model selection.
Tests reject overlapping seeds/traces and duplicate samples. They show that
changing held-out labels cannot change the tree, while changing training labels
really does change it. Reversing training row order produces identical nodes.

The learned nine-node tree differs from teacher thresholds (for example the
learned close-obstacle split is 1195 cm, not the teacher's 1200 cm). The model card
reports measured accuracy **382/384 = 99.479167%**, with two heading-class errors;
768/768 training matches. Accuracy is exact joint-class matching per held-out row,
including all stop rows, not an inflated per-output average. Confusion counts and
limitations are in [the model card](../ai/modelcard.md). This simple, correlated
synthetic distribution does not demonstrate real-world driving competence.

## Inference contract and parity

canopy_host.pilot.Pilot returns an immutable Request; it accepts no Safestop
reference and has no latch-clear operation. The JSON and self-contained generated
ai/pilot_model.h contain identical nodes/actions. The C header needs only stdint.h,
no runtime ML library, allocator, files, Python or training code.

Input order and domains (inclusive integers):
- obstacle_cm: 0–10000
- speed_cms: 0–2000
- heading_error_mdeg: -20000–20000

Outputs: speed m/s and steering degrees, classes (0,0), (4,0), (12,0), (8,-10),
(8,10). Positive steering is the demonstrator's positive-heading correction;
this is a demo convention, not calibrated vehicle geometry. The learned tree
uses obstacle and heading; speed remains an unused candidate feature. The Python
adapter rejects floats, NaN, bool and out-of-domain values. The C primitive expects
a valid three-int32 array in that domain; a future transport adapter must validate
and convert units before calling it, and must not treat invalid data as fresh.

Host C99 parity compiles ai/parity.c with -Wall -Wextra -Werror -pedantic and checks
all 1152 dataset rows, 1000 fixed-seed random vectors and 12 threshold-neighbour
vectors: **2164/2164 C/Python class and speed/steering outputs match**. Missing cc
explicitly skips that test rather than claiming parity. On this host no test skipped.
Node fields total 180 bytes and action fields 40 bytes, excluding code/compiler
padding; these are schema sizes, not runtime memory measurements.

## Veto demonstration and ownership

The pilot intentionally sees neither sensor age nor latch state. The regression
arms Safestop, obtains a learned positive speed request for a clear road, then
feeds that request with a stale speed age (31 ms). Safestop emits SAFE_STOP with
100% brake. One hundred additional pilot calls do not advance recovery or clear
the latch. Nine healthy cycles still hold it; only Safestop's tenth fresh cycle
releases it while emitting SAFE_STOP, followed by ramped RECOVER. A subsequent
out-of-envelope 21 m/s request re-latches it. This uses the existing safety API
unchanged. Learned speed/steering requests are advisory, not actuator authority.
The current host safety API has no steering veto: steering is not wired to an
actuator here, and no steering-envelope guarantee is claimed.

## Observed host verification (2026-11-03)

- Six pilot tests pass, including compiled C parity, learned-fit evidence,
  leakage rejection, exact metrics/provenance, invalid inputs and veto/latch test.
- Full existing plus pilot regression: 44 tests pass, zero skips.
- SDK/artifact gate passes; no SDK or build binaries are committed.

## Still requires SDK/target work

1. With the owner-provided licensed SDK outside git, cross-compile the header and
   parity harness for the actual QNX 8 x86_64 target; run identical vectors in the
   QEMU guest and retain target/source/toolchain evidence. Host cc success is not qcc proof.
2. Implement the target pilot process and QPP signal subscription/request adapter,
   validating units/domains and freshness; confirm the installed catalogue/overlay.
3. Run pilot at normal priority and independently run native safestop with its
   intended FIFO priority. Verify actual priority, IPC ownership and inability of
   the pilot process to reset the target latch. Python object separation alone is
   not a process-security or scheduler guarantee.
4. Exercise live stale/obstacle/invalid-request veto, N-fresh recovery and actuator
   heartbeat watchdog with the integrated CAN path; record the pilot-request /
   safety-veto evidence. Define/validate a steering envelope before any target
   steering actuation. No native runtime or target acceptance is claimed here.

No SDK/account/spend/publication/PR/video/contact action is part of this change.
