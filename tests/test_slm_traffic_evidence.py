import importlib.util,json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
from verify_slm_traffic_evidence import verify
class RestartTrafficEvidence(unittest.TestCase):
    def test_actual_saved_receipt_offline_only(self):
        self.assertTrue(verify(ROOT/"docs/acceptance/slm-traffic-20261107")["success"])
    def test_corruptions_rejected(self):
        for case in ("bytes","order","count","mainpid","pidchain","caps","unreaped"):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as folder:
                target=Path(folder)/"evidence";shutil.copytree(ROOT/"docs/acceptance/slm-traffic-20261107",target)
                path=target/("traffic1.json" if case in ("bytes","order","count") else "receipt.json")
                data=json.loads(path.read_text())
                if case=="bytes":data["host_tx"][0][1]="0000000000000000"
                elif case=="order":data["qnx_rx"].reverse()
                elif case=="count":data["host_rx"].pop()
                elif case=="mainpid":data["restarts"][0]["killed_pid"]=data["main_io_sock_pid"]
                elif case=="pidchain":data["restarts"][1]["killed_pid"]+=1
                elif case=="caps":data["caps"]["cpu.max"]="max 100000"
                else:data["guest_stopped_reaped"]=False
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):verify(target)
