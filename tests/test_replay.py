from pathlib import Path
import json
import re
import subprocess
import unittest
from canopy_host.director import hero

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'docs/replay/index.html'


class ReplayTests(unittest.TestCase):
    def test_fixture_matches_model_and_embedded_copy(self):
        text = (ROOT / 'docs/replay/run.jsonl').read_text()
        self.assertEqual([json.loads(line) for line in text.splitlines()], list(hero(7)))
        embedded = re.search(r'<script id="sample-data" type="application/json">(.*?)</script>', PAGE.read_text(), re.S)[1]
        self.assertEqual(embedded, text)

    def test_page_offline_and_explicit(self):
        page = PAGE.read_text()
        self.assertIn("connect-src 'none'", page)
        self.assertNotRegex(page, r'''(?:src|href)=["']https?://''')
        self.assertNotIn('fetch(', page)
        self.assertNotIn('WebSocket(', page)
        self.assertGreaterEqual(page.count('HOST SIMULATION / NOT QNX'), 6)
        self.assertIn('PIDs, restarts and driver stats: not recorded.', page)

    def test_javascript_parser_and_rejection(self):
        page = PAGE.read_text()
        script = re.search(r'<script id="replay-code">(.*?)</script>', page, re.S)[1]
        parser = script.split('const $ =')[0]
        harness = parser + """
const assert = require('node:assert/strict');
"""
        harness += 'const fixture = ' + json.dumps((ROOT / 'docs/replay/run.jsonl').read_text()) + ';' + chr(10)
        harness += """
assert.equal(parseReplay(fixture).length, 601);
const first = JSON.parse(fixture.split(String.fromCharCode(10))[0]);
for (const mutation of [
 {...first, source:'QNX live'}, {...first, speed_mps:-1},
 {...first, brake:101}, {...first, accepted:1}, {...first, time_ms:-1},
 {...first, scenario:'<script>'}, {...first, seed:0.5}, {...first, events:['fake']}, {...first, sequence:3}, {...first, heartbeat:{can_id:512, payload_hex:'00000000',delivered:true}}
]) assert.throws(()=>parseReplay(JSON.stringify(mutation)));
assert.throws(()=>parseReplay(''));
assert.throws(()=>parseReplay('{broken'));
assert.throws(()=>parseReplay(fixture+fixture));
assert.throws(()=>parseReplay('x'.repeat(2000001)));
console.log('Replay parser: valid fixture and malformed/source/type/order/size rejection pass');
"""
        subprocess.run(['node', '-e', harness], check=True, cwd=ROOT)
