#!/usr/bin/env python3
"""Offline host-only viewer of one pinned recorded QNX experiment. No guest/network."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote
from verify_slm_continuity import verify as continuity_verify
from native_can_three import parse_qnx

ROOT = Path(__file__).resolve().parents[1]
RUN = 'docs/acceptance/slm-continuity-20261107'
MANIFEST = 'docs/workbench/recorded-manifest.json'
# No repin command: a different capture requires explicit reviewed source changes.
MANIFEST_SHA256 = '36f4c42e48866ba3871b9254a72b1f2d2348b9cb5fc183c72c2da34ee7dc0efa'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_path(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('unsafe evidence path')
    root = Path(root).resolve()
    path = root / name
    for part in [path, *path.parents]:
        if part == root:
            break
        if part.is_symlink():
            raise ValueError('symlink evidence refused')
    if not path.resolve().is_relative_to(root):
        raise ValueError('evidence path escape')
    return path


def verify(root=ROOT):
    raw = safe_path(root, MANIFEST).read_bytes()
    if sha(raw) != MANIFEST_SHA256:
        raise ValueError('unknown recorded manifest; refusing PASS')
    manifest = json.loads(raw)
    if manifest['run'] != RUN or manifest['schema'] != 1:
        raise ValueError('unknown run/schema')
    for name, digest in manifest['files'].items():
        if sha(safe_path(root, name).read_bytes()) != digest:
            raise ValueError('corrupt/mixed evidence: ' + name)
    folder = safe_path(root, RUN)
    if {p.name for p in folder.iterdir()} != {Path(n).name for n in manifest['files'] if n.startswith(RUN + '/')}:
        raise ValueError('unexpected recorded run file set')
    summary = continuity_verify(folder)
    receipt = json.loads((folder / 'receipt.json').read_text())
    serial = (folder / 'serial.txt').read_text()
    cursor = 0
    for row in receipt['restarts']:
        kill = serial.index('# kill -9 ' + str(row['killed_pid']) + '; sleep 3;', cursor)
        end = serial.index('\nRESTART_DONE\n', kill)
        block = serial[kill:end]
        for pid, process in [(row['new_pid'], 'dev-can-linux'), (receipt['main_io_sock_pid'], 'io-sock')]:
            if not re.search(r'^\s*' + str(pid) + ' ' + process + ' ', block, re.M):
                raise ValueError('process snapshot mismatch')
        rx_end = serial.index('\nRX_DONE\n', end)
        frames = [list(x) for x in parse_qnx('\n'.join(s for s in serial[end:rx_end].splitlines() if ' TS: ' in s))]
        traffic = json.loads((folder / ('traffic%d.json' % row['run'])).read_text())
        if frames != traffic['qnx_rx'] or traffic['ordered_byte_exact'] is not True:
            raise ValueError('serial/traffic mismatch')
        cursor = serial.index('\nTX_DONE\n', rx_end)
    return dict(status='PASS', manifest=manifest, receipt=receipt, summary=summary)


def render(result, output, root=ROOT):
    """No script, remote assets, forms or runtime dependencies; escape evidence/error text."""
    esc = lambda x: html.escape(str(x), quote=True)
    def link(name, label=None):
        path = safe_path(root, name)
        url = quote(os.path.relpath(path, Path(output).parent), safe='/.-')
        return '<a href="%s">%s</a>' % (esc(url), esc(label or name))
    body = ['<h1>CANopy · Recorded incident workbench</h1>',
            '<p class="tag">RECORDED QNX EXPERIMENT · 2026-11-07 · libcan fallback</p>',
            '<p>Permanent scope: saved QNX-on-QEMU experiment, not host simulation and not a fresh native run. '
            'This host-only viewer never starts a guest or executes the saved controller.</p>',
            '<p class="warning">C6: FAIL / stopped. SocketCAN: BLOCKED / unverified. '
            'No continuous CAN availability, physical safety, certification, restart-latency or benchmark claim.</p>',
            '<p>Static snapshot: PASS describes verification at generation only. Re-run the offline verifier '
            'after evidence changes; this HTML does not monitor files or provide live integrity attestation.</p>']
    if result['status'] != 'PASS':
        body += ['<h2>UNKNOWN — bounded evidence not accepted</h2><pre>' + esc(result['error']) + '</pre>',
                 '<h3>Bounded recovery</h3><ol>'
                 '<li>Stop interpreting this capture as PASS. Preserve the failing copy and exact error; do not edit or repin hashes to silence it.</li>'
                 '<li>Compare the named file with the exact private repository revision and pinned manifest. Restore the complete matching capture into a separate clean checkout, not individual files from another run.</li>'
                 '<li>Run <code>python3 tools/incident_workbench.py --verify-only</code> there. Exit 0 accepts only the bounded recording; exit 2 remains UNKNOWN. If the matching capture is unavailable, stop here and retain UNKNOWN.</li>'
                 '<li>Only after verification, regenerate that checkout with <code>python3 tools/incident_workbench.py</code>. This does not run QNX or repair C6. Static PASS remains generation-time only.</li></ol>']
    else:
        receipt = result['receipt']
        body += ['<section aria-label="First-minute summary"><h2>In one minute: what survived?</h2>',
                 '<p><strong>Environment:</strong> a saved 7 November QNX 8-on-QEMU lab capture using the native libcan fallback, not SocketCAN. This page is a host-only offline viewer, not a live experiment.</p>',
                 '<p><strong>Killed process:</strong> the SLM-managed dev-can-linux CAN driver was killed with SIGKILL in three recorded phases; SLM started a replacement PID each time.</p>',
                 '<p><strong>Observed survivor:</strong> the main io-sock PID stayed unchanged in recorded snapshots, and the same authenticated SSH connection continued emitting counters. After each restart, 100 RX and 100 TX frames matched ordered byte-for-byte checks. This does not establish uninterrupted CAN traffic during the kill.</p>',
                 '<p><strong>Not observed/proven:</strong> continuous availability, measured restart latency, physical safety, production isolation, historical driver/source build identity, independently rehashed image, or a new native rerun. C6 FAIL / STOPPED; SocketCAN UNVERIFIED. Missing, corrupt or mixed evidence means UNKNOWN, not PASS.</p></section>',
                 '<h2>PASS — bounded recorded evidence only</h2>',
                 '<p>Same authenticated SSH connection: client PID %s; one publickey authentication, '
                 'saved counters 0–96. Main io-sock PID %s unchanged in recorded snapshots.</p>'
                 % (esc(receipt['ssh']['client_pid']), esc(receipt['main_io_sock_pid'])),
                 '<h2>Causal phases (not a shared-clock timeline)</h2>',
                 '<p>Each phase: PID check → kill → fixed 3 s settle → new PID/device snapshot → '
                 '100 RX + 100 TX ordered byte-exact checks → later tick on SAME SSH connection. '
                 'Observation windows include 3 s settle; they are NOT restart latency. '
                 'Native serial CAN TS milliseconds and host monotonic SSH seconds are separate clock domains; '
                 'no clock alignment inferred. SSH counter brackets include traffic, not just recovery.</p>']
        for row in receipt['restarts']:
            a, b = row['ssh']['counter_before'], row['ssh']['counter_after']
            ticks = receipt['ssh']['ticks']
            body += ['<section><h3>Restart %s: CAN PID %s → %s</h3>' % tuple(esc(row[k]) for k in ('run','killed_pid','new_pid')),
                     '<p>100 RX / 100 TX · ordered byte-exact · main io-sock unchanged. '
                     'Observation window including fixed 3 s settle: %s s.</p>' % esc(row['observed_seconds_including_fixed_3s_settle']),
                     '<p>Host monotonic SSH counters %s → %s (%s → %s s); same client PID %s.</p>'
                     % tuple(esc(x) for x in (a,b,ticks[a]['host_monotonic'],ticks[b]['host_monotonic'],row['ssh']['same_client_pid'])),
                     link(RUN + '/traffic%d.json' % row['run'], 'Exact four traffic arrays'), '</section>']
        body += ['<h2>Provenance and limits</h2>',
                 '<p>Exact saved controller source is hashed below; it imports native_can_three. '
                 'Current verifier/helper source hashes bind this offline review only, not historical execution. '
                 'Historical driver build identity/source binding: UNPROVEN. The image SHA256 in the receipt '
                 'is a recorded assertion only: no SDK/image/binary is bundled or independently rehashed here. '
                 'No historical source hashes are invented. SLM XML is current reference source, not proven historical image content.</p>',
                 '<p>SSH client/debug, server authentication in serial, controller, startup, routing diagnostics, '
                 'traffic and receipt are pinned together. Causal ordering comes from the saved controller and serial phases. '
                 'C6 failure receipts are pinned context, not repaired or retried. '
                 'The pin protects against accidental corruption/mixing, not an attacker able to edit this verifier.</p>',
                 '<p>' + link(MANIFEST, 'Exact SHA256 evidence manifest') + ' · pinned manifest SHA256 <code>' + esc(MANIFEST_SHA256) + '</code></p>', '<ul>']
        for name, digest in sorted(result['manifest']['files'].items()):
            body += ['<li>' + link(name) + ' <code>' + esc(digest) + '</code></li>']
        body += ['</ul>']
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>CANopy recorded incident workbench</title><style>
body{overflow-wrap:anywhere;background:#101820;color:#e6edf3;font:17px/1.6 system-ui,sans-serif;max-width:1050px;margin:auto;padding:32px}h1,h2{line-height:1.2}a{color:#7dd3fc}section{border-left:4px solid #70d6b2;padding:4px 20px;margin:24px 0;background:#17252e}.warning{border:1px solid #d5a45f;padding:16px;color:#ffe1ae}.tag{color:#70d6b2;font-weight:bold}code{overflow-wrap:anywhere;font-size:13px}li{margin:14px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}
</style></head><body>''' + '\n'.join(body) + '</body></html>\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', default='docs/workbench/index.html', help='repository-relative HTML output')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    try:
        result = verify(args.root)
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        result = dict(status='UNKNOWN', error=str(error))
    if not args.verify_only:
        if not args.output.startswith('docs/workbench/') or not args.output.endswith('.html'):
            parser.error('output must be HTML under docs/workbench/')
        output = safe_path(args.root, args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render(result, output, args.root), encoding='utf-8')
    print(result['status'] + ': bounded recorded evidence only' + (': ' + result['error'] if 'error' in result else ''))
    return 0 if result['status'] == 'PASS' else 2


if __name__ == '__main__':
    sys.exit(main())
