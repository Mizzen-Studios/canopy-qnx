import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from canopy_host.director import hero
from canopy_host.record import decode, encode, validate
ROOT = Path(__file__).resolve().parents[1]


class DirectorTests(unittest.TestCase):
    def test_deterministic_event_order_and_bytes(self):
        a, b = list(hero(7)), list(hero(7))
        self.assertEqual(encode(a), encode(b))
        self.assertEqual(len(a), 601)
        self.assertEqual(decode(encode(a)), a)
        marks = [(r['time_ms'], e) for r in a for e in r['events']]
        for mark in [(500,'heartbeat-drop-start'), (590,'watchdog-held'),
                     (3500,'heartbeat-drop-end'), (3590,'watchdog-released'),
                     (4000,'obstacle-start'), (5000,'pilot-veto-start')]:
            self.assertIn(mark, marks)
        self.assertTrue(any(r['speed_mps'] == 0 for r in a))
        self.assertTrue(all(not r['heartbeat']['delivered'] for r in a[50:350]))
        self.assertNotEqual(a[0]['speed_mps'], list(hero(5))[0]['speed_mps'])

    def test_reject_malformed_provenance_order_and_types(self):
        row = list(hero())[0]
        for key, value in [('source','QNX live'),('seed',True),('time_ms',-1),
                           ('sequence',1),('brake',101),('speed_mps',float('nan')),
                           ('events',['driver-restarted']),('accepted',1),
                           ('heartbeat',{'can_id':512,'payload_hex':'00000000','delivered':True})]:
            bad = copy.deepcopy(row); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate([bad])
        for text in ['', '{bad', encode([row])*2, 'x'*2000001]:
            with self.assertRaises(ValueError):
                decode(text)

    def test_cli_record_replay_export_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            run, page = Path(tmp)/'run.jsonl', Path(tmp)/'replay.html'
            cli = lambda *a: subprocess.run([str(ROOT/'canopy'), *map(str,a)], cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(cli('demo').returncode, 0)
            self.assertEqual(cli('record','--host-sim','--seed7','-o',run).returncode,0)
            self.assertEqual(run.read_text(),encode(hero(7)))
            self.assertNotEqual(cli('record','--host-sim','-o',run).returncode,0)
            self.assertEqual(cli('replay',run,'-o',page).returncode,0)
            self.assertIn(run.read_text(),page.read_text())
            self.assertNotEqual(cli('replay',run,'-o',page).returncode,0)
            self.assertIn('unavailable',cli('top','--replay',run).stdout)
