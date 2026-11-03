# Pilot model card — HOST SIM ONLY

Synthetic imitation learning, not independent driving/safety evaluation.
No QNX runtime inference, QPP, scheduling or vehicle validation is claimed.

- Integer inputs in order: ['obstacle_cm', 'speed_cms', 'heading_error_mdeg']. Speed is a candidate, not necessarily selected.
- Joint classes (speed m/s, steering degrees): [(0, 0), (4, 0), (12, 0), (8, -10), (8, 10)].
- Scripted demonstrator labels: generate.py; learned splits: train.py.
- CART depth cap 5, min leaf 4; 9 nodes.
- C node fields: 180 bytes plus 40 bytes of action fields;
  excludes code/compiler padding; not runtime memory measurement.
- Train: 768 rows / 24 traces; seeds 0–7.
- Held-out: 384 rows / 12 traces; seeds 100–103.
- All three families occur in both splits: unseen seeds/traces, NOT unseen families.
  Group allocation precedes sampling; no row shuffle, preprocessing or held-out tuning.
- Measured held-out joint-class accuracy: **382/384 = 99.479167%**.
  Each held-out row counts once, including stopped rows; not a trace-average.
- Confusion (rows true, columns predicted, order 0..4): [[51, 0, 0, 0, 0], [0, 87, 0, 0, 0], [0, 0, 81, 1, 1], [0, 0, 0, 77, 0], [0, 0, 0, 0, 86]].
- Train accuracy: 768/768.
- Exact dataset/source hashes and provenance: pilot_model.json.

Correlated synthetic rows, simple labels and limited coverage mean this only
measures imitation of a simplistic teacher, not real-world driving competence.
Freshness and latch state are not inputs; safestop independently vetoes.
Steering is advisory only: the host safety API checks speed, not steering.
Host rejects invalid/out-of-domain inputs; C callers must validate the same domain.
No runtime ML library; Python stdlib training. See ../docs/pilot.md for target gates.
