"""Host-only saved-artifact checks, never fresh native acceptance."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import incident_workbench as wb

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags, self.links = [], []
    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == 'a':
            self.links.append(dict(attrs)['href'])

class Workbench(unittest.TestCase):
    def fixture(self, root):
        manifest = json.loads((ROOT / wb.MANIFEST).read_text())
        for name in [wb.MANIFEST, *manifest['files']]:
            dest = root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)

    def test_recording(self):
        result = wb.verify()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['summary']['restarts'], 3)
        self.assertEqual(result['receipt']['main_io_sock_pid'], 163853)

    def test_tampering(self):
        for kind in ('corrupt', 'missing', 'truncate', 'mixed', 'false', 'string', 'integer', 'extra', 'controller', 'auth', 'manifest', 'repinned'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self.fixture(root)
                folder = root / wb.RUN
                path = folder / 'traffic2.json'
                if kind == 'corrupt':
                    path.write_bytes(path.read_bytes() + b' ')
                elif kind == 'missing':
                    path.unlink()
                elif kind == 'truncate':
                    path.write_bytes(path.read_bytes()[:100])
                elif kind == 'mixed':
                    shutil.copyfile(ROOT / wb.RUN / 'traffic1.json', path)
                elif kind in ('false', 'string', 'integer'):
                    path = folder / 'receipt.json'
                    data = json.loads(path.read_text())
                    data['success'] = {'false': False, 'string': 'true', 'integer': 1}[kind]
                    path.write_text(json.dumps(data))
                elif kind == 'extra':
                    (folder / 'another-run.json').write_text('{}')
                elif kind == 'controller':
                    (folder / 'controller.py').write_text('# replacement')
                elif kind == 'auth':
                    (folder / 'ssh-debug.txt').write_text('forged publickey')
                else:
                    path = root / wb.MANIFEST
                    data = json.loads(path.read_text())
                    if kind == 'manifest':
                        data['files']['../escape'] = '0' * 64
                    else:
                        target = folder / 'receipt.json'
                        target.write_text('{}')
                        data['files'][wb.RUN + '/receipt.json'] = wb.sha(target.read_bytes())
                    path.write_text(json.dumps(data))
                with self.assertRaises((ValueError, OSError)):
                    wb.verify(root)
                p = subprocess.run([sys.executable, str(ROOT / 'tools/incident_workbench.py'), '--root', str(root)], capture_output=True, text=True)
                self.assertEqual(p.returncode, 2)
                self.assertIn('UNKNOWN', p.stdout)
                self.assertNotIn('<h2>PASS', (root / 'docs/workbench/index.html').read_text())

    def test_escape_and_symlink(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ('../escape', '/absolute', 'docs/../../escape', ''):
                with self.assertRaises(ValueError):
                    wb.safe_path(root, name)
            (root / 'link').symlink_to(ROOT, target_is_directory=True)
            with self.assertRaises(ValueError):
                wb.safe_path(root, 'link/README.md')
            self.fixture(root)
            target = root / wb.RUN / 'receipt.json'
            target.unlink()
            target.symlink_to(ROOT / wb.RUN / 'receipt.json')
            with self.assertRaises(ValueError):
                wb.verify(root)

    def test_saved_unknown_review_fixtures(self):
        folder = ROOT / 'docs/acceptance/unknown-review-20261107'
        receipt = json.loads((folder / 'receipt.json').read_text())
        self.assertEqual({c['variant'] for c in receipt['cases']}, {'missing','corrupt','mixed'})
        self.assertEqual(receipt['verifier_sha256'], wb.sha((ROOT/'tools/incident_workbench.py').read_bytes()))
        for case in receipt['cases']:
            page = folder / case['html']
            self.assertEqual(case['exit'], 2)
            self.assertIn('UNKNOWN', case['outcome'])
            self.assertEqual(case['html_sha256'], wb.sha(page.read_bytes()))
            self.assertIn('<h2>UNKNOWN', page.read_text())
            self.assertNotIn('<h2>PASS', page.read_text())
            self.assertIn('Bounded recovery', page.read_text())

    def test_output_confinement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.fixture(root)
            for output in ('README.html', 'docs/workbench/../../escape.html'):
                p = subprocess.run([sys.executable, str(ROOT / 'tools/incident_workbench.py'), '--root', str(root), '--output', output], capture_output=True, text=True)
                self.assertNotEqual(p.returncode, 0)
                self.assertFalse((root / 'escape.html').exists())
                self.assertFalse((root / 'README.html').exists())

    def test_html_escaping(self):
        payload = '<script>alert("x")</script>&'
        result = dict(status='UNKNOWN', error=payload)
        page = wb.render(result, ROOT / 'docs/workbench/index.html')
        self.assertNotIn(payload, page)
        self.assertIn('&lt;script&gt;', page)
        for phrase in ('Bounded recovery', 'do not edit or repin', 'separate clean checkout', '--verify-only', 'retain UNKNOWN', 'generation-time only'):
            self.assertIn(phrase, page)
        result = copy.deepcopy(wb.verify())
        result['receipt']['restarts'][0]['killed_pid'] = payload
        page = wb.render(result, ROOT / 'docs/workbench/index.html')
        self.assertNotIn(payload, page)
        self.assertIn('&lt;script&gt;', page)

    def test_generated_html_inspection(self):
        path = ROOT / 'docs/workbench/index.html'
        rendered = wb.render(wb.verify(), path)
        self.assertEqual(path.read_text(), rendered)
        page = Page()
        page.feed(rendered)
        self.assertEqual(page.tags.count('section'), 3)
        self.assertFalse({'script', 'iframe', 'form', 'img'} & set(page.tags))
        for href in page.links:
            self.assertNotIn('://', href)
            self.assertTrue((path.parent / unquote(href)).is_file(), href)
        for phrase in ('C6: FAIL / stopped', 'SocketCAN: BLOCKED / unverified', 'UNPROVEN', 'NOT restart latency', 'separate clock domains', 'not host simulation', 'static', '626715 → 778263', '778263 → 2764823', '2764823 → 4743191'):
            self.assertIn(phrase.lower(), rendered.lower())

if __name__ == '__main__':
    unittest.main()
