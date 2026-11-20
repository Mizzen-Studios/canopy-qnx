"""HOST-only portable bundle and clean-checkout regression."""
import base64,hashlib,importlib.util,json,re,shutil,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('portable',ROOT/'tools/build_portable_desk.py')
portable=importlib.util.module_from_spec(spec);spec.loader.exec_module(portable)
class PortableDesk(unittest.TestCase):
    def test_deterministic_public_only_bundle(self):
        for path,raw in portable.build().items():self.assertEqual(path.read_bytes(),raw)
        body=(ROOT/'docs/downloads/canopy-incident-desk.html').read_text()
        self.assertNotIn('<script src=',body);self.assertNotIn('<link rel="stylesheet"',body)
        self.assertNotIn('/home/ubuntu',body);self.assertNotIn('recording-20261115d/',body)
        self.assertIn("connect-src 'none'",body)
        encoded=body.split('globalThis.CANopyPublicDownloads=',1)[1].split(';for(const pack',1)[0]
        packs=json.loads(encoded);self.assertEqual(len(packs),2)
        self.assertEqual(len({p['name'] for p in packs}),2)
        for p in packs:
            raw=base64.b64decode(p['base64']);self.assertEqual(raw,(ROOT/p['source']).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(),p['sha256'])
    def test_node_suite_leaves_fresh_checkout_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            fresh=Path(tmp)/'fresh'
            shutil.copytree(ROOT,fresh,ignore=shutil.ignore_patterns('.git','.openclaw','__pycache__','build','dist'))
            before={str(p.relative_to(fresh)) for p in fresh.rglob('*') if p.is_file()}
            files=sorted(str(p.relative_to(fresh)) for p in (fresh/'tests/incident_pack').glob('*.test.js'))
            result=subprocess.run(['node','--test',*files],cwd=fresh,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertFalse((fresh/'.openclaw').exists())
            self.assertEqual(before,{str(p.relative_to(fresh)) for p in fresh.rglob('*') if p.is_file()})
