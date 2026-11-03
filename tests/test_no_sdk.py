from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NoSDKTests(unittest.TestCase):
    def fixture(self, name, data, stage=False, erase=False, symlink=False):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / 'scripts').mkdir()
            for script in ('check-no-sdk.sh', 'check_no_sdk.py'):
                (root / 'scripts' / script).write_bytes((ROOT / 'scripts' / script).read_bytes())
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if symlink:
                path.symlink_to('/nonexistent')
            else:
                path.write_bytes(data)
            if stage:
                subprocess.run(['git', '-C', str(root), 'add', '-f', name], check=True)
            if erase:
                path.unlink()
            result = subprocess.run(['sh', 'scripts/check-no-sdk.sh'], cwd=root,
                                    capture_output=True, text=True)
            return result.returncode, result.stderr

    def test_clean_text(self):
        self.assertEqual(self.fixture('docs/a.md', b'original host project')[0], 0)

    def test_paths_content_symlink(self):
        for name, data, link in [('sdk/a.h', b'text', False),
                                 ('BOOT.IFS', b'text', False),
                                 ('payload.txt', bytes([127])+b'ELF'+bytes([0]), False),
                                 ('qnx800/a', b'text', False),
                                 ('archive.txt', b'PK'+bytes([3,4]), False),
                                 ('a.h', b'QNX Software '+b'Development Platform', False),
                                 ('link', b'', True)]:
            self.assertNotEqual(self.fixture(name, data, symlink=link)[0], 0, name)

    def test_staged_blob_after_delete(self):
        self.assertNotEqual(self.fixture('hidden.txt', bytes([0]), stage=True, erase=True)[0], 0)

    def test_unusual_filename(self):
        self.assertNotEqual(self.fixture('space'+chr(10)+' name.so', b'text', stage=True)[0], 0)
