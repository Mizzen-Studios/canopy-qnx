import copy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from canopy_host.check import (EvidenceError, check, compare_candump,
    load_budgets, load_evidence, parse_budgets, parse_candump,
    render_rustc, render_github_annotations, render_github_summary)
ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/budgets'

class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.b = load_budgets(ROOT / 'budgets.yaml')
        self.e = load_evidence(FIXTURES / 'host-sim-pass.json')

    def test_pass_boundary(self):
        r = check(self.b, self.e)
        self.assertTrue(r.passed)
        self.assertEqual(r.exit_code, 0)
        self.assertEqual([r.line for r in r.results], [2, 3, 4, 5])
        self.assertEqual(render_github_annotations(r), '')

    def test_four_failures_and_renderers(self):
        r = check(self.b, load_evidence(FIXTURES / 'host-sim-fail.json'))
        self.assertFalse(r.passed)
        self.assertEqual(r.exit_code, 1)
        for code in ('CP101', 'CP102', 'CP103', 'CP104'):
            self.assertIn('error[' + code + ']', render_rustc(r))
            self.assertIn('title=' + code, render_github_annotations(r))
        summary = render_github_summary(r)
        for token in ('mermaid', 'HOST SIM', 'BLOCKED', 'target evidence: **none**'):
            self.assertIn(token, summary)

    def test_missing_evidence_fails_closed(self):
        for e in ({}, None, [], load_evidence(FIXTURES / 'host-sim-insufficient.json')):
            self.assertEqual([x.status for x in check(self.b, e).results], ['fail'] * 4)
        for key, index in [('deadline_samples_ms', 0), ('restart_chain_ms', 1), ('overruns', 2), ('actual_candump', 3), ('expected_candump', 3)]:
            e = copy.deepcopy(self.e); del e[key]
            self.assertEqual(check(self.b, e).results[index].status, 'fail')

    def test_provenance(self):
        for key, values in [('source', ['QNX', 'HOST', '', None, {}]), ('target_evidence', ['QNX', None]), ('version', [True, 1.0, 2])]:
            for value in values:
                self.assertEqual([r.status for r in check(self.b, dict(self.e, **{key:value})).results], ['fail'] * 4)
        self.assertTrue(check(self.b, dict(self.e, source='HOST VCAN')).passed)

    def test_nonfinite_unused_metadata_fails_closed(self):
        e = dict(self.e, metadata={'nested': [float('nan')]})
        self.assertEqual([r.status for r in check(self.b, e).results], ['fail'] * 4)

    def test_invalid_observations(self):
        for value in [float('nan'), float('inf'), -float('inf'), -1, True, '1', None, 10**400]:
            e = copy.deepcopy(self.e); e['deadline_samples_ms'] = [value]
            self.assertEqual(check(self.b, e).results[0].status, 'fail')
            e = copy.deepcopy(self.e); e['restart_chain_ms']['driver_up'] = value
            self.assertEqual(check(self.b, e).results[1].status, 'fail')
            e = copy.deepcopy(self.e); e['overruns'] = value
            self.assertEqual(check(self.b, e).results[2].status, 'fail')
        for samples in [[], {}, None, 10]:
            self.assertEqual(check(self.b, dict(self.e, deadline_samples_ms=samples)).results[0].status, 'fail')
        for hops in [{}, [], {'first_frame': 1}]:
            self.assertEqual(check(self.b, dict(self.e, restart_chain_ms=hops)).results[1].status, 'fail')
        self.assertEqual(check(self.b, dict(self.e, overruns=0.0)).results[2].status, 'fail')

    def test_strict_yaml(self):
        text = (ROOT / 'budgets.yaml').read_text()
        for bad in [text + 'overruns: 1\n', text + 'unknown: 1\n', text.replace('version: 1', 'version: 2'),
                    text.replace('true', 'false'), text.replace('30', '.nan'), text.replace('30', '1e3'),
                    text.replace('30', 'Infinity'), text.replace('30', '-1'), text.replace('30', 'true'),
                    text.replace('30', '01'), text.replace('30', '1x3'), text.replace('30', '"30"'),
                    text.replace('overruns: 0', 'overruns: 0.0'), text.replace('30', '&alias 30'),
                    text.replace('30', '9'*400), text.replace('deadline_ms:', ' deadline_ms:')]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_budgets(bad)
        self.assertEqual(parse_budgets('# comment\n' + text).lines, (3,4,5,6))
        with self.assertRaises(EvidenceError):
            check(replace(self.b, deadline_ms=float('nan')), self.e)

    def test_json_nonfinite_duplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'e.json'
            for text in ['{"x":NaN}', '{"x":Infinity}', '{"x":1e999}', '{"x":1,"x":2}']:
                p.write_text(text)
                with self.assertRaises(EvidenceError):
                    load_evidence(p)

    def test_annotation_and_summary_escape(self):
        r = check(replace(self.b, path='bad,%\n::error injected'), {})
        annotations = render_github_annotations(r)
        self.assertEqual(len(annotations.splitlines()), 4)
        self.assertIn('%2C%25%0A', annotations)
        r = replace(r, results=(replace(r.results[0], observed='<script>|\n' + chr(96)*3),))
        summary = render_github_summary(r)
        self.assertNotIn('<script>', summary)
        self.assertIn('&#124;', summary)
        self.assertIn('&#96;', summary)

class CandumpTests(unittest.TestCase):
    def test_human_and_compact(self):
        for left, right in [('vcan0 123#', 'can0 123 [0]'),
                            ('(123.000001) vcan0 123#00AAff', 'can0 123 [3] 00 AA FF'),
                            ('vcan0 123#R8', 'can0 123 [8] remote request'),
                            ('vcan0 1FFFFFFF#FF', 'can0 1fffffff [1] ff')]:
            self.assertIsNone(compare_candump(left, right))

    def test_id_dlc_payload_and_order(self):
        for left, right in [('x 123#00', 'y 124#00'), ('x 123#00', 'y 00000123#00'),
                            ('x 123#00', 'y 123#0000'), ('x 123#00', 'y 123#01'),
                            ('x 123#R1', 'y 123#R2'), ('x 123#R1', 'y 123#00'),
                            ('x 123#00\nx 124#01', 'y 124#01\ny 123#00'),
                            ('x 123#00\nx 124#01', 'y 123#00'),
                            ('x 123#00', 'y 123#00\ny 123#00')]:
            self.assertIsNotNone(compare_candump(left, right))

    def test_malformed_rejected_never_skipped(self):
        for text in ['', '   ', 'comment', 'x 800#00', 'x 20000000#00', 'x 123#0',
                     'x 123##100', 'x 123#' + '00'*9, 'x 123 [2] 00', 'x 123 [1] ZZ',
                     'x 123 [9] 00', 'x 123#00\nmalformed', '(nan) x 123#00']:
            with self.subTest(text=text), self.assertRaises(EvidenceError):
                parse_candump(text)

if __name__ == '__main__':
    unittest.main()
