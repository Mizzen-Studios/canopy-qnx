"""Offline review coverage and absent-binding regressions; never launches runtime."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('review_claims', ROOT / 'tools/review_claims.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class ReviewClaimsTests(unittest.TestCase):
    def test_document_coverage_and_paths(self):
        packet = review.generate()
        for rel in packet['documents']:
            expected = review.units(ROOT / rel)
            actual = [r for r in packet['occurrences'] if r['path'] == rel]
            self.assertEqual([(r['line'], r['text']) for r in actual], [(line, text) for line, text, _ in expected])
            self.assertTrue(actual)
        for group in packet['families'].values():
            self.assertTrue(group['evidence_paths'])
            self.assertTrue(group['gap'])
            for path in group['evidence_paths']:
                self.assertEqual(packet['artifacts'][path]['sha256'], review.digest(ROOT / path))

    def test_absent_historical_identity_not_invented(self):
        packet = review.generate()
        for name in ('libcan', 'slm', 'traffic', 'continuity'):
            self.assertIsNone(packet['families'][name]['tested_source_commit'])
            self.assertIsNone(packet['families'][name]['binary_sha256'])
            self.assertTrue(packet['families'][name]['image_sha256'])
        self.assertEqual(packet['families']['c6']['label'], 'UNVERIFIED')
        self.assertIn('STOPPED', packet['families']['c6']['gap'])
        self.assertTrue(packet['families']['c6']['binary_sha256'])
        self.assertTrue(packet['families']['host-suite']['tested_source_commit'])

    def test_visible_parser_excludes_executable_text(self):
        p = review.Visible()
        p.feed('<p>host <b>only</b></p><script>fake PASS</script><style>hidden</style><button>Play</button>')
        p.flush()
        self.assertEqual([text for _, text in p.rows], ['host only', 'Play'])
        self.assertEqual(review.bindings({'image_sha256':'a'*64})[0]['pointer'], '/image_sha256')
