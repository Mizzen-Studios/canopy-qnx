"""SDK-free Node schema/CLI checks included in the existing host suite."""
import pathlib
import shutil
import subprocess
import unittest


class IncidentPackTests(unittest.TestCase):
    def test_shared_core_and_cli(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node 22+ is required for the reusable incident-pack host core")
        root = pathlib.Path(__file__).resolve().parents[1]
        result = subprocess.run([node, "--test", "tests/incident_pack/core.test.js", "tests/incident_pack/native.test.js", "tests/incident_pack/historical.test.js"], cwd=root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
