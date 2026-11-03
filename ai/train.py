"""Deterministic stdlib CART and self-contained C99 table export."""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from .generate import ACTIONS, FEATURES, SOURCE
ROOT = Path(__file__).resolve().parents[1]
MAX_DEPTH, MIN_LEAF = 5, 4


def validate(rows):
    groups = {s: set() for s in ('train', 'heldout')}
    seeds = {s: set() for s in groups}
    seen = set()
    for r in rows:
        if r['split'] not in groups or r['source'] != SOURCE:
            raise ValueError('invalid split/source')
        key = (r['trace'], r['time_ms'])
        if key in seen:
            raise ValueError('duplicate sample')
        seen.add(key)
        groups[r['split']].add(r['trace'])
        seeds[r['split']].add(r['seed'])
        if (len(r['features']) != 3 or any(type(x) is not int for x in r['features'])
                or type(r['action']) is not int or not 0 <= r['action'] < len(ACTIONS)):
            raise ValueError('invalid sample')
    if (any(not g for g in groups.values()) or groups['train'] & groups['heldout']
            or seeds['train'] & seeds['heldout']):
        raise ValueError('empty split or trace/seed leakage')


def impurity(rows):
    return len(rows) - sum(Fraction(n * n, len(rows))
                           for n in Counter(r['action'] for r in rows).values())


def fit(rows):
    if not rows or any(r['split'] != 'train' for r in rows):
        raise ValueError('fit requires exclusively training rows')
    nodes = []

    def grow(samples, depth):
        counts = Counter(r['action'] for r in samples)
        action = min(counts, key=lambda a: (-counts[a], a))
        index = len(nodes)
        nodes.append(dict(feature=-1, threshold=0, left=-1, right=-1, action=action))
        if depth >= MAX_DEPTH or len(counts) == 1:
            return index
        best = None
        parent_score = impurity(samples)
        for feature in range(3):
            values = sorted({r['features'][feature] for r in samples})
            for low, high in zip(values, values[1:]):
                threshold = (low + high) // 2
                left = [r for r in samples if r['features'][feature] <= threshold]
                right = [r for r in samples if r['features'][feature] > threshold]
                if min(len(left), len(right)) < MIN_LEAF:
                    continue
                candidate = (impurity(left) + impurity(right), feature, threshold)
                if candidate[0] < parent_score and (best is None or candidate < best):
                    best = candidate
        if best is not None:
            _, feature, threshold = best
            left = grow([r for r in samples if r['features'][feature] <= threshold], depth + 1)
            right = grow([r for r in samples if r['features'][feature] > threshold], depth + 1)
            nodes[index].update(feature=feature, threshold=threshold, left=left, right=right)
        return index

    grow(rows, 0)
    return nodes


def predict(nodes, features):
    index = 0
    while nodes[index]['feature'] >= 0:
        n = nodes[index]
        index = n['left'] if features[n['feature']] <= n['threshold'] else n['right']
    return nodes[index]['action']


def evaluate(nodes, rows):
    matrix = [[0] * len(ACTIONS) for _ in ACTIONS]
    for r in rows:
        matrix[r['action']][predict(nodes, r['features'])] += 1
    correct = sum(matrix[i][i] for i in range(len(ACTIONS)))
    return dict(correct=correct, total=len(rows), accuracy=correct / len(rows), confusion=matrix)


def header(model):
    lines = ['/* HOST SIM learned model; no QNX runtime validation. */',
             '#ifndef CANOPY_PILOT_MODEL_H', '#define CANOPY_PILOT_MODEL_H', '#include <stdint.h>',
             'typedef struct { int32_t feature, threshold, left, right, action; } canopy_pilot_node;',
             'static const canopy_pilot_node canopy_pilot_nodes[] = {']
    for n in model['nodes']:
        lines.append('    {' + ', '.join(str(n[k]) for k in ('feature', 'threshold', 'left', 'right', 'action')) + '},')
    lines += ['};', 'typedef struct { int32_t speed_mps, steering_deg; } canopy_pilot_request;',
              'static const canopy_pilot_request canopy_pilot_actions[] = {']
    lines += [f'    {{{speed}, {steering}}},' for speed, steering in ACTIONS]
    lines += ['};', 'static inline int canopy_pilot_action(const int32_t features[3]) {',
              '    int i = 0;', '    while (canopy_pilot_nodes[i].feature >= 0) {',
              '        const canopy_pilot_node *n = &canopy_pilot_nodes[i];',
              '        i = features[n->feature] <= n->threshold ? n->left : n->right;',
              '    }', '    return canopy_pilot_nodes[i].action;', '}',
              'static inline canopy_pilot_request canopy_pilot_infer(const int32_t features[3]) {',
              '    return canopy_pilot_actions[canopy_pilot_action(features)];', '}', '#endif', '']
    return chr(10).join(lines)


def main():
    path = ROOT / 'ai/sim_logs.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    validate(rows)
    train = [r for r in rows if r['split'] == 'train']
    heldout = [r for r in rows if r['split'] == 'heldout']
    nodes = fit(train)
    sources = ['ai/generate.py', 'ai/train.py', 'canopy_host/pilot.py', 'canopy_host/safety.py']
    model = dict(schema=1, source=SOURCE, features=FEATURES, actions=ACTIONS, nodes=nodes,
                 training=dict(algorithm='CART Gini; rational scores; deterministic ties',
                               max_depth=MAX_DEPTH, min_leaf=MIN_LEAF,
                               split='seeds 0..7 train; 100..103 heldout; whole traces',
                               base_revision='19ccc7b',
                               dataset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                               source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}),
                 metrics={s: evaluate(nodes, data) for s, data in [('train', train), ('heldout', heldout)]})
    (ROOT / 'ai/pilot_model.json').write_text(json.dumps(model, indent=2, sort_keys=True) + chr(10))
    (ROOT / 'ai/pilot_model.h').write_text(header(model))
    m = model['metrics']['heldout']
    card = f'''# Pilot model card — HOST SIM ONLY

Synthetic imitation learning, not independent driving/safety evaluation.
No QNX runtime inference, QPP, scheduling or vehicle validation is claimed.

- Integer inputs in order: {FEATURES}. Speed is a candidate, not necessarily selected.
- Joint classes (speed m/s, steering degrees): {ACTIONS}.
- Scripted demonstrator labels: generate.py; learned splits: train.py.
- CART depth cap {MAX_DEPTH}, min leaf {MIN_LEAF}; {len(nodes)} nodes.
- C node fields: {len(nodes) * 20} bytes plus {len(ACTIONS) * 8} bytes of action fields;
  excludes code/compiler padding; not runtime memory measurement.
- Train: {len(train)} rows / {len(set(r['trace'] for r in train))} traces; seeds 0–7.
- Held-out: {len(heldout)} rows / {len(set(r['trace'] for r in heldout))} traces; seeds 100–103.
- All three families occur in both splits: unseen seeds/traces, NOT unseen families.
  Group allocation precedes sampling; no row shuffle, preprocessing or held-out tuning.
- Measured held-out joint-class accuracy: **{m['correct']}/{m['total']} = {m['accuracy']:.6%}**.
  Each held-out row counts once, including stopped rows; not a trace-average.
- Confusion (rows true, columns predicted, order 0..4): {m['confusion']}.
- Train accuracy: {model['metrics']['train']['correct']}/{len(train)}.
- Exact dataset/source hashes and provenance: pilot_model.json.

Correlated synthetic rows, simple labels and limited coverage mean this only
measures imitation of a simplistic teacher, not real-world driving competence.
Freshness and latch state are not inputs; safestop independently vetoes.
Steering is advisory only: the host safety API checks speed, not steering.
Host rejects invalid/out-of-domain inputs; C callers must validate the same domain.
No runtime ML library; Python stdlib training. See ../docs/pilot.md for target gates.
'''
    (ROOT / 'ai/modelcard.md').write_text(card)
    print(json.dumps(model['metrics'], sort_keys=True))


if __name__ == '__main__':
    main()
