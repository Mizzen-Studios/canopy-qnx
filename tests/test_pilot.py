import copy
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import unittest
from ai.generate import generate, ACTIONS
from ai.train import validate, fit, predict, evaluate, header
from canopy_host.pilot import Pilot
from canopy_host.safety import Safestop, Inputs
from canopy_host.protocol import State

ROOT = Path(__file__).resolve().parents[1]


class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [json.loads(s) for s in (ROOT / 'ai/sim_logs.jsonl').read_text().splitlines()]
        cls.model = json.loads((ROOT / 'ai/pilot_model.json').read_text())
        cls.train = [r for r in cls.rows if r['split'] == 'train']
        cls.heldout = [r for r in cls.rows if r['split'] == 'heldout']

    def test_dataset_generation_and_groups(self):
        self.assertEqual(generate(), self.rows)
        validate(self.rows)
        for key in ('seed', 'trace'):
            self.assertFalse({r[key] for r in self.train} & {r[key] for r in self.heldout})
        self.assertEqual((len(self.train), len(self.heldout)), (768, 384))
        for field in ('seed', 'trace'):
            bad = copy.deepcopy(self.rows)
            bad[-1][field] = bad[0][field]
            with self.assertRaises(ValueError):
                validate(bad)
        with self.assertRaises(ValueError):
            validate(self.rows + [self.rows[0]])

    def test_fit_is_learned_reproducible_and_train_only(self):
        nodes = fit(self.train)
        self.assertEqual(nodes, self.model['nodes'])
        self.assertEqual(fit(list(reversed(self.train))), nodes)
        with self.assertRaises(ValueError):
            fit(self.rows)
        # Altering held-out labels cannot alter trained nodes.
        changed = copy.deepcopy(self.rows)
        for r in changed:
            if r['split'] == 'heldout':
                r['action'] = (r['action'] + 1) % len(ACTIONS)
        self.assertEqual(fit([r for r in changed if r['split'] == 'train']), nodes)
        # Conversely training labels really determine the exported policy.
        relabelled = [dict(r, action=0) for r in self.train]
        self.assertNotEqual(fit(relabelled), nodes)
        self.assertEqual(len(fit(relabelled)), 1)

    def test_metrics_denominators_and_export(self):
        for split, rows in [('train', self.train), ('heldout', self.heldout)]:
            measured = evaluate(self.model['nodes'], rows)
            self.assertEqual(measured, self.model['metrics'][split])
            self.assertEqual(sum(map(sum, measured['confusion'])), len(rows))
            self.assertEqual(measured['accuracy'], measured['correct'] / len(rows))
        self.assertEqual((ROOT / 'ai/pilot_model.h').read_text(), header(self.model))
        self.assertEqual(hashlib.sha256((ROOT / 'ai/sim_logs.jsonl').read_bytes()).hexdigest(),
                         self.model['training']['dataset_sha256'])
        for path, digest in self.model['training']['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)

    def test_invalid_inputs(self):
        pilot = Pilot()
        for x in [(-1, 0, 0), (10001, 0, 0), (100, 2001, 0),
                  (100, 0, 20001), (True, 0, 0), (float('nan'), 0, 0), (100., 0, 0)]:
            with self.assertRaises(ValueError):
                pilot.request(*x)

    def test_learned_drive_request_veto_and_latch_ownership(self):
        pilot, stop = Pilot(), Safestop()
        for i in range(20):
            stop.cycle(i * 10, Inputs())
        self.assertFalse(stop.latched)
        request = pilot.request(10000, 1000, 0)
        self.assertGreater(request.speed_mps, 0)
        # A stale sensor is invisible to pilot: its positive request is vetoed.
        packet = stop.cycle(200, Inputs(speed_age_ms=31, pilot_speed_mps=request.speed_mps))
        self.assertEqual((packet.state, packet.brake, stop.latched), (State.SAFE_STOP, 100, True))
        for _ in range(100):
            pilot.request(10000, 1000, 0)
        self.assertTrue(stop.latched)
        self.assertEqual(stop.fresh_cycles, 0)
        for i in range(9):
            packet = stop.cycle(210 + i * 10, Inputs(pilot_speed_mps=request.speed_mps))
            self.assertEqual(packet.state, State.SAFE_STOP)
            self.assertTrue(stop.latched)
        packet = stop.cycle(300, Inputs(pilot_speed_mps=request.speed_mps))
        self.assertEqual(packet.state, State.SAFE_STOP)
        self.assertFalse(stop.latched)  # Only safestop's tenth fresh cycle releases.
        self.assertEqual(stop.cycle(310, Inputs()).state, State.RECOVER)
        self.assertEqual(stop.cycle(320, Inputs(pilot_speed_mps=21)).state, State.SAFE_STOP)
        self.assertTrue(stop.latched)

    def test_compiled_c_parity_all_rows_random_and_split_boundaries(self):
        cc = shutil.which('cc')
        if not cc:
            self.skipTest('host C compiler missing; C parity unverified')
        vectors = [r['features'] for r in self.rows]
        rng = random.Random(713)
        vectors += [[rng.randrange(10001), rng.randrange(2001), rng.randrange(-20000, 20001)]
                    for _ in range(1000)]
        for n in self.model['nodes']:
            if n['feature'] >= 0:
                for delta in (-1, 0, 1):
                    x = [5000, 1000, 0]
                    x[n['feature']] = n['threshold'] + delta
                    vectors.append(x)
        with tempfile.TemporaryDirectory(prefix='.parity-', dir=ROOT / 'ai') as directory:
            binary = Path(directory) / 'parity'
            subprocess.run([cc, '-std=c99', '-Wall', '-Wextra', '-Werror', '-pedantic',
                            str(ROOT / 'ai/parity.c'), '-o', str(binary)], check=True)
            data = chr(10).join(' '.join(map(str, x)) for x in vectors) + chr(10)
            result = subprocess.run([str(binary)], input=data, text=True, capture_output=True, check=True)
        outputs = [tuple(map(int, line.split())) for line in result.stdout.splitlines()]
        expected = []
        pilot = Pilot()
        for x in vectors:
            action = predict(self.model['nodes'], x)
            request = pilot.request(*x)
            expected.append((action, request.speed_mps, request.steering_deg))
            self.assertEqual((request.speed_mps, request.steering_deg), tuple(ACTIONS[action]))
        self.assertEqual(outputs, expected)


if __name__ == '__main__':
    unittest.main()
