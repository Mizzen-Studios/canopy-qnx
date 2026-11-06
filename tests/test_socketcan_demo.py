"""Original native demo CLI checks; live checks require a dedicated vcan interface."""
import os
from pathlib import Path
import socket
import struct
import subprocess
import time
import unittest

BINARY = os.environ.get("CANOPY_DEMO_BINARY")

@unittest.skipUnless(BINARY, "set CANOPY_DEMO_BINARY to externally built native demo")
class DemoCLI(unittest.TestCase):
    def run_demo(self, *args):
        return subprocess.run([BINARY, *args], capture_output=True, text=True, timeout=3)

    def test_usage(self):
        self.assertEqual(self.run_demo().returncode, 2)

    def test_invalid_mode(self):
        self.assertEqual(self.run_demo("bad", "none", "1").returncode, 2)

    def test_invalid_counts(self):
        for count in ["0", "-1", "1001", "abc", "1x", "", "999999999999999999999999"]:
            with self.subTest(count=count):
                self.assertEqual(self.run_demo("rx", "none", count).returncode, 2)

    def test_missing_interface(self):
        self.assertEqual(self.run_demo("rx", "no_such_can99", "1").returncode, 1)

    @unittest.skipUnless(os.environ.get("CANOPY_DEMO_VCAN"), "explicit dedicated vcan required")
    def test_live_rx_tx_and_mismatch(self):
        interface = os.environ["CANOPY_DEMO_VCAN"]
        with socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW) as bus:
            bus.bind((interface,))
            bus.settimeout(5)
            rx = subprocess.Popen([BINARY, "rx", interface, "100"], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True)
            try:
                self.assertIn("RX_READY", rx.stdout.readline())
                for _ in range(100):
                    bus.send(struct.pack("=IB3x8s", 0x123, 8, bytes(range(1,9))))
                    time.sleep(.003)
                out, err = rx.communicate(timeout=5)
                self.assertEqual(rx.returncode, 0, err)
                self.assertIn("RX_EXACT observed=100/100 result=PASS", out)
            finally:
                if rx.poll() is None:
                    rx.kill(); rx.communicate()
            tx = subprocess.Popen([BINARY, "tx", interface, "100"], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True)
            try:
                observed = []
                while len(observed) < 100:
                    cid, length, payload = struct.unpack("=IB3x8s", bus.recv(16))
                    if cid == 0x321:
                        observed.append((length, payload))
                out, err = tx.communicate(timeout=5)
                self.assertEqual(tx.returncode, 0, err)
                self.assertEqual(observed, [(8, bytes.fromhex("1122334455667788"))]*100)
                self.assertIn("TX_ACCEPTED observed=100/100 result=PASS", out)
            finally:
                if tx.poll() is None:
                    tx.kill(); tx.communicate()
            bad = subprocess.Popen([BINARY, "rx", interface, "1"], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
            try:
                self.assertIn("RX_READY", bad.stdout.readline())
                bus.send(struct.pack("=IB3x8s", 0x123, 8, bytes(8)))
                out, err = bad.communicate(timeout=5)
                self.assertEqual(bad.returncode, 1)
                self.assertIn("payload mismatch", err)
                self.assertIn("observed=0/1 result=FAIL", out)
            finally:
                if bad.poll() is None:
                    bad.kill(); bad.communicate()
