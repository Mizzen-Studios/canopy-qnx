#!/usr/bin/env python3
"""Offline private review coverage; reads repository text only, never runs guests."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs/review-claims.json'
BASE = '32a4ae17b8401e30590437a68f86f403f802c315'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Family references are supporting material, NOT blanket acceptance of a paragraph.
# Per-occurrence labels below keep absent historical binding UNVERIFIED.
SPECS = {
 'new-native-recorder': ('observed in this QEMU run', ['docs/acceptance/native-recorder-20261108/*', 'docs/acceptance/control-fix-20261108/*', 'native/incident_recorder.c', 'tools/collect_native_incident.py'], 'Fresh capture source d913faffb3ebd83d11f65c44c50437154b3450ec with original ELF/IFS/disk and collector bindings in incident.json/receipt.json; no SSH continuity, adversarial isolation or continuous CAN guarantee.'),
 'new-desk': ('host-only', ['docs/incident-pack-receipts/*', 'docs/acceptance/control-fix-20261108/*', 'docs/incident-pack.md', 'tools/incident_pack/*.js', 'web/incident-pack/*', 'tests/incident_pack/*'], 'Schema v2 control binding and new derived native pack: control-fix-20261108; historical v1 remains unchanged and now UNKNOWN. Reusable import/query/export host and browser behavior only; HOST fixtures synthetic. Origin declarations and cooperative binding are not attestation.'),
 'prereq': ('observed in this QEMU run', ['docs/acceptance/prereq-20261108/*'], 'Exact source/ELF/IFS/disk in receipt.json. Slog2 and control probes only, not managed libcan acceptance. Path enforcement BLOCKED; redacted logs preserve original hashes separately.'),
 'libcan': ('observed in this QEMU run', ['docs/acceptance/native-can-20261106/*'], 'Historical source commit and driver binary hash absent; recorded image assertion only.'),
 'slm': ('observed in this QEMU run', ['docs/acceptance/slm-20261107/*'], 'PID snapshots only; SSH UNVERIFIED; historical source/driver binary binding absent.'),
 'traffic': ('observed in this QEMU run', ['docs/acceptance/slm-traffic-20261107/*'], 'Post-restart traffic only; SSH UNVERIFIED; historical source/driver binary binding absent.'),
 'continuity': ('observed in this QEMU run', ['docs/acceptance/slm-continuity-20261107/*', 'docs/workbench/recorded-manifest.json'], 'Bounded authenticated stream only. Historical source commit/driver binary absent. No image independently rehashed.'),
 'c6': ('UNVERIFIED', ['docs/acceptance/safestop-build-20261107/*', 'docs/acceptance/safestop-failure-20261107/*', 'docs/acceptance/safestop-focused-failure-20261107/*'], 'Compile-only source/output hashes; native runtime FAIL / STOPPED, no accepted scenarios, no retries. No tested source commit recorded.'),
 'viewer': ('host-only', ['docs/acceptance/workbench-20261107.json', 'docs/acceptance/unknown-review-20261107/*', 'docs/acceptance/browser-20261107/*', 'tools/incident_workbench.py', 'tests/test_incident_workbench.py'], 'Static generation-time evidence; UNKNOWN is rejection, never target proof. External screenshot hashes not rechecked here.'),
 'replay': ('host-only', ['docs/replay/run.jsonl', 'docs/replay/verification.md', 'tests/test_replay.py', 'tests/test_replay_browser.cjs', 'tests/test_director.py', 'canopy_host/director.py', 'canopy_host/record.py'], 'Historical replay browser source/compiled-browser binding UNVERIFIED; current parser/model tests are host-only.'),
 'model': ('host-only', ['tests/test_safety.py', 'tests/test_sim.py', 'tests/test_native_safestop.py', 'canopy_host/protocol.py', 'canopy_host/safety.py', 'canopy_host/sim.py', 'docs/test-results.txt'], 'Logical/model parameters only, not native safety or physics/timing validation; compiled host binary hash absent.'),
 'vcan': ('host-only', ['docs/host-runtime-evidence-20261103/*/*', 'docs/host-vcan-setup.md', 'tests/test_runtime.py', 'canopy_host/socketcan.py', 'canopy_host/runtime.py'], 'Saved Linux raw logs only; historical tested source commit/binary hashes absent. Current optional live tests skipped.'),
 'vss': ('host-only', ['tests/test_vss.py', 'canopy_host/vss.py', 'dbc/*', 'vss/*'], 'Host codec checks only; target QPP integration UNVERIFIED.'),
 'pilot': ('host-only', ['tests/test_pilot.py', 'ai/pilot_model.json', 'ai/pilot_model.h', 'ai/modelcard.md', 'canopy_host/pilot.py'], 'Synthetic held-out host model and host C parity only; target inference/QPP UNVERIFIED; host binary hash absent.'),
 'doctor': ('host-only', ['tests/test_doctor.py', 'canopy_host/doctor.py', 'tests/test_session.py', 'canopy'], 'Mocked/probe contract tests do not prove current host readiness, SDK validity or target acceptance.'),
 'guard': ('host-only', ['scripts/check-no-sdk.sh', 'scripts/check_no_sdk.py', 'tests/test_no_sdk.py', '.github/workflows/host-tests.yml', 'LICENSE'], 'Heuristic guard, not provenance certification; no runtime binaries/images applicable. Originality/legal provenance not independently attested.'),
 'host-suite': ('host-only', ['docs/acceptance/final-upgrade-20261108/*', 'docs/acceptance/host-review-20261107/*', 'docs/acceptance/browser-20261107/receipt.json', 'docs/acceptance/browser-20261107/host-tests.log', 'docs/test-results.txt'], 'Exact declared historical commits only; current review execution in docs/acceptance/private-review-20261107/. No target acceptance.'),
 'blocked': ('UNVERIFIED', ['docs/socketcan-demo.md', 'docs/socketcan-x86-gate-20261104.md', 'docs/vss-qpp-integration.md', 'docs/capabilities.json', 'docs/acceptance/safestop-focused-failure-20261107/receipt.json'], 'No matching native SocketCAN ABI/QPP/QSTI/full C3/safety acceptance. Documentation is a boundary, not a receipt.'),
 'scope': ('UNVERIFIED', ['docs/capabilities.json', 'docs/incident-workbench.md', 'REVIEW.md'], 'Context, instructions or negative scope, not affirmative tested capability. No receipt establishes broader availability/safety/timing or historical source identity.')
}


def families(text, section, path):
    t = (text + ' ' + section).lower()
    found = set()
    rules = {
      'new-native-recorder': ['native-recorder', 'reusable native', 'new native', 'fresh source-bound capture', 'bounded slog2'],
      'new-desk': ['incident desk', 'incident pack', 'incident-pack', 'byo', 'cooperative', 'collector declaration'],
      'prereq': ['prereq-20261108', 'slog2', 'ability control', 'co-located', 'attach/connect'],
      'libcan': ['native-can-', 'three native libcan', 'three ordered', '100-frame'],
      'slm': ['slm-20261107', '278546', 'managed-process restarts'],
      'traffic': ['slm-traffic-', 'follow-up 11', 'three additional'],
      'continuity': ['ssh', 'continuity', 'authenticated', 'causal phases', 'restart 1:', 'restart 2:', 'restart 3:'],
      'c6': ['c6', '850', 'safestop-build-', 'fifo', 'heartbeat'],
      'viewer': ['viewer', 'workbench', 'chromium', 'unknown', 'corrupt', 'missing/corrupt', 'recorded-manifest'],
      'replay': ['replay', 'dashboard', 'scrub', 'play/pause', 'hero', 'keyboard', 'event-jump'],
      'model': ['model', 'crc', 'counter', 'latch', 'deceleration', 'simulation', 'deterministic', 'timeout recovery'],
      'vcan': ['vcan', 'socketcan(interface', 'linux can', 'linux transport', 'independent processes'],
      'vss': ['dbc', 'vss', 'codec'],
      'pilot': ['pilot', 'learned', 'synthetic', 'c export'],
      'doctor': ['doctor', 'preflight', 'host_ready', 'qnx_host', 'qnx_target', 'binfmt', 'qemu version', 'five-second', 'environment'],
      'guard': ['hygiene', 'no-sdk', 'apache', 'licence', 'license', 'sdk detector', 'original host', 'gpl', 'ci runs', 'ci requires'],
      'host-suite': ['host suite', 'full-suite', 'regression', '126', '133', '134', '125 pass', 'host tests'],
      'blocked': ['socketcan', 'qpp', 'qsti', 'unverified', 'full c3', 'least privilege', 'production', 'certification', 'availability', 'benchmark']
    }
    for family, terms in rules.items():
        if any(term in t for term in terms):
            found.add(family)
    if path == 'docs/replay/index.html':
        found.add('replay')
    if path == 'docs/workbench/index.html':
        found.add('viewer')
    return sorted(found or {'scope'})


class Visible(HTMLParser):
    def __init__(self):
        super().__init__(); self.skip = 0; self.rows = []; self.parts = []; self.line = 1
    def flush(self):
        text = ' '.join(' '.join(self.parts).split())
        if text:
            self.rows.append((self.line, text))
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if not self.skip and tag in ('p','li','h1','h2','h3','button','label','option','td','th','pre','section','div'):
            self.flush()
    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip -= 1
        elif not self.skip and tag in ('p','li','h1','h2','h3','button','label','option','td','th','pre','section','div'):
            self.flush()
    def handle_data(self, text):
        if not self.skip and text.strip():
            if not self.parts:
                self.line = self.getpos()[0]
            self.parts.append(text)


def units(path):
    if path.suffix == '.html':
        parser = Visible(); parser.feed(path.read_text()); parser.flush()
        return [(line, text, '') for line, text in parser.rows]
    rows = []; block = []; start = 0; section = ''
    for number, line in enumerate(path.read_text().splitlines() + [''], 1):
        if line.startswith('#'):
            if block:
                rows.append((start, '\n'.join(block), section)); block = []
            section = line
        if line.strip():
            if not block:
                start = number
            block.append(line)
        elif block:
            rows.append((start, '\n'.join(block), section)); block = []
    return rows


def bindings(value, pointer=''):
    out = []
    if isinstance(value, dict):
        for key, item in value.items():
            here = pointer + '/' + key.replace('~', '~0').replace('/', '~1')
            if isinstance(item, str) and (re.fullmatch('[0-9a-f]{40}|[0-9a-f]{64}', item)):
                out.append({'pointer': here, 'value': item})
            out += bindings(item, here)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            out += bindings(item, pointer + '/' + str(i))
    return out


def generate():
    groups = {}; artifacts = {}
    for name, (label, globs, gap) in SPECS.items():
        paths = sorted({p.relative_to(ROOT).as_posix() for g in globs for p in ROOT.glob(g) if p.is_file()})
        groups[name] = dict(label=label, evidence_paths=paths, gap=gap,
                            tested_source_commit=None, binary_sha256=None, image_sha256=None,
                            binding_note='Null unless explicitly declared in indexed artifact bindings. Receipt-import Git revision is NOT tested source.')
        for rel in paths:
            p = ROOT / rel
            artifact = {'sha256': digest(p), 'kind': 'supporting source/document; not runtime receipt'}
            if '/acceptance/' in rel or '/host-runtime-evidence-' in rel or rel == 'docs/test-results.txt':
                artifact['kind'] = 'saved evidence; scope/binding must be read, not inferred'
            if p.suffix == '.json':
                artifact['declared_bindings'] = bindings(json.loads(p.read_text()))
            artifacts[rel] = artifact
    for name, group in groups.items():
        declared = [dict(artifact=rel, **binding) for rel in group['evidence_paths']
                    for binding in artifacts[rel].get('declared_bindings', [])]
        group['recorded_bindings'] = declared
        group['tested_source_commit'] = [b for b in declared if len(b['value']) == 40 and
            any(key in b['pointer'] for key in ('source_commit', '/source', 'baseline'))] or None
        group['image_sha256'] = [b for b in declared if 'image' in b['pointer'].lower()] or None
        group['binary_sha256'] = [b for b in declared if 'output_sha256' in b['pointer']] or None
    paths = ['docs/native-recorder.md', 'docs/incident-pack.md', 'web/incident-pack/index.html', 'README.md', 'STATUS.md', 'docs/workbench/index.html', 'docs/replay/index.html', 'docs/private-demo.md', 'docs/proof-capture/SCRIPT.md']
    occurrences = []
    for rel in paths:
        for line, text, section in units(ROOT / rel):
            refs = families(text, section, rel)
            occurrences.append(dict(path=rel, line=line, text=text, families=refs,
                                    labels=sorted({groups[f]['label'] for f in refs} | ({'UNKNOWN'} if 'unknown' in text.lower() else set())),
                                    historical_source_binding='UNVERIFIED unless exact declared field in referenced evidence; no commit inferred'))
    return dict(schema='canopy-private-review.v1', reviewed_tip=BASE,
                boundaries='Offline text/evidence inspection only. No QEMU/SDK/guest/live CAN/network runtime. C6 STOPPED. No safety/timing/availability claims.',
                coverage='All nonempty Markdown paragraphs (including code/instructions) and all visible HTML text blocks. Supporting families may overlap: none grant blanket acceptance. Embedded replay behavior covered by replay tests, never target acceptance.',
                codelab='Not present in this repository; EDU is out of write/read scope for this packet.',
                documents={rel: digest(ROOT / rel) for rel in paths},
                labels={'observed in this QEMU run':'Historical bounded raw capture only; not this review executing QNX.', 'host-only':'Host implementation/test or browser evidence only.', 'UNKNOWN':'Rejected missing/corrupt/mixed input, no accepted native timeline.', 'UNVERIFIED':'No adequate capability or exact historical source/binary/image binding. Null is not invented.'},
                families=groups, artifacts=artifacts, occurrences=occurrences)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--write', action='store_true'); args = parser.parse_args()
    content = json.dumps(generate(), ensure_ascii=False, separators=(',', ':')) + '\n'
    if args.write:
        DEST.write_text(content)
    elif not DEST.is_file() or DEST.read_text() != content:
        raise SystemExit('FAIL: review appendix stale; inspect claims then --write')
    print('PASS: exhaustive text occurrence mapping; absent bindings remain UNVERIFIED')


if __name__ == '__main__':
    main()
