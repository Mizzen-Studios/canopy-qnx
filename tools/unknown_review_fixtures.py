#!/usr/bin/env python3
"""Generate disposable host-only UNKNOWN pages from mutated temporary captures."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import incident_workbench as wb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/acceptance/unknown-review-20261107'

def generate():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT/wb.MANIFEST).read_text())
    rows = []
    scratch = ROOT / '.git/unknown-review-tmp'
    scratch.mkdir(parents=True, exist_ok=True)
    for variant in ('missing', 'corrupt', 'mixed'):
        with tempfile.TemporaryDirectory(prefix='canopy-unknown-', dir=scratch) as temp:
            root = Path(temp)
            for name in [wb.MANIFEST, *manifest['files']]:
                dest = root/name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT/name, dest)
            target = root/wb.RUN/'traffic2.json'
            before = hashlib.sha256(target.read_bytes()).hexdigest()
            if variant == 'missing':
                target.unlink()
                mutation = 'Remove traffic2.json from temporary capture'
            elif variant == 'corrupt':
                target.write_bytes(target.read_bytes()+b' ')
                mutation = 'Append one ASCII space to temporary traffic2.json'
            else:
                shutil.copyfile(root/wb.RUN/'traffic1.json', target)
                mutation = 'Replace temporary traffic2.json with traffic1.json (wrong phase/run)'
            command = [sys.executable, str(ROOT/'tools/incident_workbench.py'), '--root', str(root), '--output', 'docs/workbench/unknown.html']
            result = subprocess.run(command, capture_output=True, text=True)
            page = (root/'docs/workbench/unknown.html').read_text()
            assert result.returncode == 2 and '<h2>UNKNOWN' in page and '<h2>PASS' not in page
            assert 'Bounded recovery' in page and 'generation-time only' in page
            # Normalize only the disposable root in the diagnostic, not its meaning.
            output = result.stdout.replace(str(root), '<TEMP_ROOT>')
            page = page.replace(str(root), '&lt;TEMP_ROOT&gt;')
            path = OUT/(variant+'.html')
            path.write_text(page)
            rows.append(dict(variant=variant, input=wb.RUN+'/traffic2.json', mutation=mutation, original_sha256=before, mutated_sha256=hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None, command='python3 tools/incident_workbench.py --root <TEMP_ROOT> --output docs/workbench/unknown.html', exit=result.returncode, outcome=output.strip(), html=path.name, html_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    receipt = dict(scope='Disposable generated UNKNOWN review fixtures; no native execution; not authoritative PASS artifact', base_revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(), source_binding='Exact generator/verifier hashes below; base revision alone may precede uncommitted generator edits', generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), verifier_sha256=hashlib.sha256((ROOT/'tools/incident_workbench.py').read_bytes()).hexdigest(), manifest_sha256=wb.MANIFEST_SHA256, reproduce='python3 tools/unknown_review_fixtures.py', cases=rows)
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS: three disposable UNKNOWN pages; authoritative capture unchanged')

if __name__ == '__main__':
    generate()
