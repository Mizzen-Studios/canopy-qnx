"""Linux owned-child proof and synthetic policy tests: NOT QNX/SLM evidence."""
import copy
from pathlib import Path
import subprocess
import selectors
import sys
import tempfile
import unittest
from canopy_host.supervision import RestartBudget, validate_restart, validate_slm

CONFIG = Path(__file__).resolve().parents[1] / 'config/supervision/slm-can-fallback.xml'


def fixture():
    return dict(source='host fixture NOT QNX',
                main_before=dict(pid=20, instance='main-1', executable='dummy-main'),
                main_after=dict(pid=20, instance='main-1', executable='dummy-main'),
                can_before=dict(pid=21, instance='can-1', executable='dummy-can'),
                killed=dict(pid=21, instance='can-1', executable='dummy-can'),
                can_after=dict(pid=22, instance='can-2', executable='dummy-can'),
                traffic_resumed=True, driver_ready=True, ssh={})


class SupervisionTests(unittest.TestCase):
    def test_rolling_window_and_latch(self):
        budget = RestartBudget()
        self.assertEqual([budget.request(i) for i in range(5)], [1, 2, 4, 8, 16])
        self.assertIsNone(budget.request(5))
        self.assertIsNone(budget.request(1000))
        with self.assertRaises(ValueError):
            budget.manual_reset(driver_stopped=False, safestop_latched=True)
        budget.manual_reset(driver_stopped=True, safestop_latched=True)
        self.assertEqual(budget.request(1001), 1)
        b = RestartBudget()
        for i in range(5):
            b.request(i)
        self.assertEqual(b.request(60), 16)  # t=0 expires exactly at 60s

    def test_bad_clocks(self):
        for now in (-1, float('nan'), float('inf'), True, '1'):
            with self.assertRaises(ValueError):
                RestartBudget().request(now)
        b = RestartBudget()
        b.request(10)
        with self.assertRaises(ValueError):
            b.request(9)

    def test_config_is_dedicated_and_fail_closed(self):
        self.assertTrue(validate_slm(CONFIG))
        data = CONFIG.read_text()
        for bad in (data.replace('dev-can-linux', 'io-sock'),
                    data.replace('restart', 'none'),
                    data.replace('<SLM:args>-b id=0,freq=500k</SLM:args>', ''),
                    data.replace('</SLM:component>', '<SLM:args>-b id=0,freq=500k</SLM:args></SLM:component>'),
                    '<!DOCTYPE x>' + data):
            with tempfile.TemporaryDirectory() as root:
                p = Path(root) / 'bad.xml'
                p.write_text(bad)
                with self.assertRaises(ValueError):
                    validate_slm(p)

    def test_pid_is_not_ssh_or_socketcan_evidence(self):
        result = validate_restart(fixture())
        self.assertFalse(result['ssh_uninterrupted'])
        self.assertFalse(result['full_c3'])
        self.assertFalse(result['socketcan'])
        with self.assertRaises(ValueError):
            validate_restart(fixture(), require_qnx=True)
        r = fixture()
        r['ssh'] = dict(authenticated=True, same_connection=True, continuous_probe=True, drops=0)
        self.assertTrue(validate_restart(r)['ssh_uninterrupted'])
        for key in ('authenticated', 'same_connection', 'continuous_probe'):
            r['ssh'][key] = False
            self.assertFalse(validate_restart(r)['ssh_uninterrupted'])
            r['ssh'][key] = True

    def test_identity_and_readiness_rejections(self):
        for key, field, value in [('killed', 'pid', 20), ('main_after', 'instance', 'reused'),
                                  ('can_after', 'pid', 21), ('can_before', 'pid', -1),
                                  ('can_after', 'instance', 'can-1'),
                                  ('can_after', 'executable', 'another')]:
            r = copy.deepcopy(fixture())
            r[key][field] = value
            with self.assertRaises(ValueError):
                validate_restart(r)
        for key in ('driver_ready', 'traffic_resumed'):
            r = fixture()
            r[key] = False
            with self.assertRaises(ValueError):
                validate_restart(r)

    def test_three_actual_owned_child_restarts_not_qnx(self):
        # Popen objects retain child ownership; no PID-file lookup, name kill,
        # Linux procfs assumption on QNX, or arbitrary process signaling.
        program = 'import sys; print("READY", flush=True); [print(x.strip(), flush=True) for x in sys.stdin]'
        children = []
        def line(p):
            with selectors.DefaultSelector() as selector:
                selector.register(p.stdout, selectors.EVENT_READ)
                self.assertTrue(selector.select(3), 'owned child response timeout')
                return p.stdout.readline().strip()
        def spawn():
            p = subprocess.Popen([sys.executable, '-u', '-c', program],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            children.append(p)
            self.assertEqual(line(p), 'READY')
            return p
        def ping(p, text):
            p.stdin.write(text + '\n')
            p.stdin.flush()
            self.assertEqual(line(p), text)
        try:
            main = spawn()
            can = spawn()
            for i in range(3):
                old = can.pid
                ping(main, 'main-before-' + str(i))
                can.kill()  # exact owned CAN stand-in only
                self.assertEqual(can.wait(timeout=3), -9)
                can = spawn()
                self.assertNotEqual(old, can.pid)
                ping(can, 'fresh-dummy-traffic-' + str(i))
                self.assertIsNone(main.poll())
                ping(main, 'main-after-' + str(i))
        finally:
            for p in children:
                if p.poll() is None:
                    p.terminate()
                p.wait(timeout=3)
                p.stdin.close()
                p.stdout.close()
