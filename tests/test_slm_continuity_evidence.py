"""Offline saved-evidence tests, not fresh QNX/SSH tests."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from verify_slm_continuity import verify

class ContinuityEvidence(unittest.TestCase):
    def test_saved_receipt(self):
        self.assertEqual(verify(ROOT/'docs/acceptance/slm-continuity-20261107')['restarts'],3)
    def test_corruptions_refused(self):
        for kind in ('client','counter','clock','auth','server','stream','timeout'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                folder=Path(temp)/'capture';shutil.copytree(ROOT/'docs/acceptance/slm-continuity-20261107',folder)
                p=folder/'receipt.json';r=json.loads(p.read_text())
                if kind=='client':r['restarts'][1]['ssh']['same_client_pid']+=1
                if kind=='counter':r['ssh']['ticks'][5]['counter']=0
                if kind=='clock':r['ssh']['ticks'][5]['host_monotonic']=0
                p.write_text(json.dumps(r))
                if kind in ('auth','timeout'):
                    p=folder/'ssh-debug.txt';s=p.read_text();p.write_text(s.replace('Authenticated to','NOT AUTHENTICATED') if kind=='auth' else s+'not responding')
                if kind=='server':
                    p=folder/'serial.txt';p.write_text(p.read_text().replace('Accepted publickey for root','AUTH REMOVED'))
                if kind=='stream':
                    p=folder/'ssh-stream.txt';p.write_text(p.read_text()+'SSH_TICK_0'+chr(10))
                with self.assertRaises(ValueError):verify(folder)
