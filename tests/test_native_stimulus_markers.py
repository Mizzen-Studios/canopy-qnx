"""Host-only unit fixtures; no guest/native acceptance claims."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location('native_host', Path(__file__).parents[1]/'tools/native_safestop_host.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class StimulusMarkers(unittest.TestCase):
    def test_stale_three_second_interval_and_real_action_markers(self):
        bus = MagicMock()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/'actions.jsonl'
            with patch.object(module, 'SocketCAN', return_value=bus), patch.object(module.time,'sleep'), patch.object(module.time,'monotonic',side_effect=[0,0,2,5,6]), patch.object(module.time,'monotonic_ns',side_effect=[100,200]):
                module.stimulus('fixture-only',6,'stale',events=output)
            rows = [json.loads(s) for s in output.read_text().splitlines()]
        self.assertEqual([r['event'] for r in rows],['fault-start','sensors-restored'])
        self.assertEqual([r['monotonic_ns'] for r in rows],[100,200])
        self.assertTrue(all(r['scenario']=='stale-none' for r in rows))
        self.assertEqual(bus.send.call_count,4)  # at0 and5 only; none at2
        bus.close.assert_called_once()
