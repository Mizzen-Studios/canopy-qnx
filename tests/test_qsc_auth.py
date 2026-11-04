import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
class PrivateQSCAuth(unittest.TestCase):
    def setup_run(self, root):
        secrets=root/"secrets";secrets.mkdir(mode=0o700)
        secret=secrets/"myqnx";secret.write_text("synthetic-test-only-value");secret.chmod(0o600)
        mock=root/"mock.py"
        mock.write_text("#!/usr/bin/env python3\nimport os,sys,pathlib,json\np=pathlib.Path(sys.argv[1][1:]); rows=p.read_text().splitlines()\nassert rows[0]=='-myqnx.user' and rows[2]=='-myqnx.password' and len(rows)==4\nassert 'MYQNX_PASSWORD' not in os.environ\nassert rows[3] not in repr(sys.argv)\npathlib.Path(os.environ['RESULT']).write_text(json.dumps(sys.argv))\nprint(rows[3])\n")
        mock.chmod(0o700)
        env={**os.environ,"MYQNX_USER":"synthetic-user","MYQNX_SECRET_FILE":str(secret),"QSC_CLI":str(mock),"QSC_PRIVATE_DIR":str(root/"private"),"RESULT":str(root/"result.json")}
        return secret,env
    def test_private_options_no_argv_or_stdout_leak_and_cleanup(self):
        with tempfile.TemporaryDirectory(dir="/var/tmp") as folder:
            root=Path(folder);secret,env=self.setup_run(root)
            result=subprocess.run([str(ROOT/"scripts/qsc-auth.sh"),"-listLicenseKeys"],env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertNotIn(secret.read_text(),result.stdout+result.stderr+(root/"result.json").read_text())
            self.assertFalse(list((root/"private").glob("options.*")))
            log=list((root/"private").glob("qsc-log.*"))[0]
            self.assertEqual(log.stat().st_mode&0o777,0o600)
            self.assertEqual((root/"private").stat().st_mode&0o777,0o700)
    def test_missing_permissive_multiline_and_repository_fail_closed(self):
        for case in ("missing","permissive","multiline","repository","symlink"):
            with self.subTest(case=case),tempfile.TemporaryDirectory(dir="/var/tmp") as folder:
                root=Path(folder);secret,env=self.setup_run(root)
                if case=="missing":secret.unlink()
                elif case=="permissive":secret.chmod(0o644)
                elif case=="multiline":secret.write_text("synthetic\nsecond")
                elif case=="repository":(root/".git").mkdir()
                else:
                    target=secret.with_name("target");secret.rename(target);secret.symlink_to(target)
                result=subprocess.run([str(ROOT/"scripts/qsc-auth.sh")],env=env,capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0)
                self.assertFalse((root/"result.json").exists())
                self.assertNotIn("synthetic-test-only-value",result.stdout+result.stderr)
                self.assertFalse(list((root/"private").glob("options.*")))
