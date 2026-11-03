import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from canopy_host.live_record import validate, convert, SCHEMA
from canopy_host.record import encode, decode
from canopy_host.runtime import SOURCE
from canopy_host.session import RotatingLog
from canopy_host.safety import Safestop, Inputs
from canopy_host.pilot import Pilot
from canopy_host.protocol import Heartbeat, State


class SessionTests(unittest.TestCase):
    def row(self):
        return dict(schema=SCHEMA, source=SOURCE, clock='host-monotonic-ns',
                    scenario='host-session', sequence=0, monotonic_ns=100, origin_ns=100,
                    time_ms=0., interface='vcan0', sender_pid=123, actuator_pid=456,
                    speed_mps=10., brake=100, hazards=True, watchdog=True,
                    safestop=True, accepted=False, events=[],
                    inputs=dict(speed_age_ms=1, obstacle_age_ms=1, obstacle_m=100, pilot_speed_mps=10),
                    heartbeat=dict(can_id=512, payload_hex=Heartbeat(State.SAFE_STOP, 100, 0).encode().hex(), delivered=False))

    def test_record_roundtrip_and_fail_closed(self):
        r = self.row()
        self.assertEqual(decode(encode([r])), [r])
        for key, value in [('source', 'host deterministic simulation; NOT QNX'), ('clock', 'logical-ms'),
                           ('monotonic_ns', True), ('time_ms', 2), ('sender_pid', None),
                           ('schema', 'QNX'), ('brake', float('nan'))]:
            bad = dict(r, **{key: value})
            with self.assertRaises(ValueError, msg=key):
                decode(json.dumps(bad))
        with self.assertRaises(ValueError):
            validate([r, dict(r, sequence=1)])

    def test_browser_live_schema_contract(self):
        r = self.row()
        page = Path('docs/replay/index.html').read_text()
        script = page.split('<script id="replay-code">')[1].split('const $ =')[0]
        program = script + "\nconst r=" + json.dumps(r) + "; parseReplay(JSON.stringify(r));"
        program += "for(const key of ['clock','source','monotonic_ns','interface','sender_pid']){const bad={...r,[key]:null};let rejected=false;try{parseReplay(JSON.stringify(bad))}catch{rejected=true}if(!rejected)throw Error(key);}"
        subprocess.run(['node', '-e', program], check=True)

    def test_rotation_bound(self):
        with tempfile.TemporaryDirectory() as d:
            log = RotatingLog(Path(d)/'test', limit=40, backups=2)
            for i in range(100):
                log.write(json.dumps(dict(i=i))+'\n')
                log.flush()
            log.close()
            self.assertEqual(len(list(Path(d).iterdir())), 3)
            self.assertTrue(all(p.stat().st_size <= 40 for p in Path(d).iterdir()))

    def test_pilot_cannot_clear_obstacle_latch(self):
        stop = Safestop()
        request = Pilot().request(10000, 1000, 0)
        for t in range(0, 500, 10):
            p = stop.cycle(t, Inputs(obstacle_m=1, pilot_speed_mps=request.speed_mps))
            self.assertTrue(stop.latched)
            self.assertEqual(p.brake, 100)

    @unittest.skipUnless(os.environ.get('CANOPY_LIVE_VCAN') == '1', 'opt-in actual vcan')
    def test_live_session_vss_replay_and_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)/'run'
            subprocess.run([sys.executable, '-m', 'canopy_host.session', '--duration', '1.5',
                            '--interface', os.environ.get('CANOPY_VCAN_INTERFACE', 'vcan0'),
                            '--output', str(out)], check=True)
            rows = convert(out)
            self.assertGreater(len(rows), 15)
            self.assertEqual(decode(encode(rows)), rows)
            raw = [json.loads(x) for x in (out/'session.jsonl').read_text().splitlines()]
            self.assertEqual({r['can_id'] for r in raw if r['event']=='vss-update'}, {256,257,258})
            agents = [r for r in raw if r['event']=='host-agent']
            gaps = [(b['monotonic_ns']-a['monotonic_ns'])/1e6 for a,b in zip(agents, agents[1:])]
            self.assertLess(max(gaps), 100)
            self.assertTrue(any(not r['safestop'] for r in rows))
            self.assertFalse((out/'session.pid').exists())
            self.assertEqual(raw[-1]['event'], 'cleanup')
            for pid in (rows[0]['sender_pid'], rows[0]['actuator_pid']):
                with self.assertRaises(ProcessLookupError):
                    os.kill(pid, 0)

    @unittest.skipUnless(os.environ.get('CANOPY_LIVE_VCAN') == '1', 'opt-in actual vcan')
    def test_live_pilot_obstacle_veto(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)/'run'
            subprocess.run([sys.executable, '-m', 'canopy_host.session', '--duration', '0.7',
                            '--obstacle', '1', '--output', str(out)], check=True)
            rows = convert(out)
            self.assertTrue(all(r['safestop'] and r['brake']==100 for r in rows))


if __name__ == '__main__':
    unittest.main()
