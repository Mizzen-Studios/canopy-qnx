import subprocess
import tempfile
from pathlib import Path
import unittest

class CheckCLI(unittest.TestCase):
    def test_pass_fail_summary_and_missing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            summary = Path(directory)/"summary.md"
            base = ["./canopy", "check"]
            good = subprocess.run(base+["tests/fixtures/budgets/host-sim-pass.json", "--github", "--summary", str(summary)], capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertIn("HOST SIM", good.stdout)
            self.assertIn("CP104", summary.read_text())
            self.assertIn("mermaid", summary.read_text())
            bad = subprocess.run(base+["tests/fixtures/budgets/host-sim-fail.json", "--github"], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 1)
            self.assertIn("::error", bad.stdout)
            missing = subprocess.run(base+[str(Path(directory)/"absent.json")], capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2)
            self.assertNotIn("ok[CP", missing.stdout)
            insufficient = subprocess.run(base+["tests/fixtures/budgets/host-sim-insufficient.json"], capture_output=True, text=True)
            self.assertEqual(insufficient.returncode, 1)
