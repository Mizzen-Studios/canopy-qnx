"""Read-only host preflight. Presence/help probes are not guest acceptance."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


class Host:
    """Small injectable boundary; never execute SDK tools or source environment scripts."""
    env = os.environ

    def which(self, name):
        return shutil.which(name)

    def read(self, path):
        try:
            return Path(path).read_text()[:16384]
        except (OSError, UnicodeError):
            return ''

    def exists(self, path):
        return Path(path).exists()

    def external(self, path, directory=False):
        try:
            resolved = Path(path).expanduser().resolve(strict=True)
            if resolved == ROOT or ROOT in resolved.parents:
                return False
            return resolved.is_dir() if directory else resolved.is_file() and resolved.stat().st_size > 0
        except (OSError, ValueError, RuntimeError):
            return False

    def run(self, argv):
        try:
            result = subprocess.run(argv, capture_output=True, text=True, timeout=5,
                                    env={**self.env, 'LC_ALL': 'C'})
            return result.returncode, (result.stdout + result.stderr)[:16384]
        except (OSError, subprocess.TimeoutExpired) as error:
            return 1, type(error).__name__


def diagnose(host=None):
    h = host or Host()
    checks = []

    def add(name, passed, detail, required=True, scope='host'):
        checks.append(dict(id=name, scope=scope, status='pass' if passed else
                           ('blocked' if required else 'info'), required=required, detail=detail))

    add('platform', sys.platform == 'linux',
        f'{platform.system()} {platform.machine()}; x86_64 guest via TCG, no KVM required')
    qemu = h.which('qemu-system-x86_64')
    rc, version = h.run([qemu, '--version']) if qemu else (1, 'qemu-system-x86_64 not found on PATH')
    add('qemu.version', rc == 0 and 'QEMU emulator version' in version, version.splitlines()[0] if version else 'No version output')
    probes = [('qemu.tcg', ['-accel', 'help'], r'^tcg$', 'TCG accelerator'),
              ('qemu.edu', ['-device', 'help'], r'name "edu"', 'edu device'),
              ('qemu.edu.dma_mask', ['-device', 'edu,help'], r'^\s*dma_mask=', 'edu dma_mask property'),
              ('qemu.kvaser_pci', ['-device', 'help'], r'name "kvaser_pci"', 'kvaser_pci device'),
              ('qemu.can-host-socketcan', ['-object', 'help'], r'^\s*can-host-socketcan\s*$', 'can-host-socketcan object')]
    cache = {}
    for name, args, pattern, label in probes:
        key = tuple(args)
        if key not in cache:
            cache[key] = h.run([qemu, *args]) if qemu else (1, 'QEMU missing')
        rc, output = cache[key]
        passed = rc == 0 and bool(re.search(pattern, output, re.M))
        add(name, passed, f'{label} advertised by QEMU help' if passed else
            f'{label} unavailable (probe exit {rc}); install a compatible QEMU build')
    add('kvm', h.exists('/dev/kvm'), '/dev/kvm present' if h.exists('/dev/kvm') else
        '/dev/kvm absent; accepted: use -accel tcg for the x86_64 guest', required=False)

    user = h.which('qemu-x86_64-static') or h.which('qemu-x86_64')
    rc, output = h.run([user, '--version']) if user else (1, '')
    add('user-emulator', rc == 0 and 'qemu-x86_64 version' in output,
        output.splitlines()[0] if output else 'x86_64 user emulator absent; required for x86_64 Linux SDK tools on ARM64',
        required=platform.machine() in ('aarch64', 'arm64'))
    registration = h.read('/proc/sys/fs/binfmt_misc/qemu-x86_64')
    enabled = h.read('/proc/sys/fs/binfmt_misc/status').strip() == 'enabled'
    registered = enabled and registration.startswith('enabled\n') and bool(re.search(
        r'^interpreter (?:.*qemu-x86_64[^\n]*|.*/qemu-binfmt/x86_64-binfmt[^\n]*)$', registration, re.M))
    add('binfmt.x86_64', registered,
        'Enabled x86_64 binfmt registration; not an SDK execution test' if registered else
        'No enabled qemu-x86_64 binfmt registration; explicit user-emulator invocation remains possible', required=False)
    for tool in ('ip', 'candump', 'cansend', 'cangen'):
        path = h.which(tool)
        add(f'tool.{tool}', bool(path), path or f'{tool} missing; install iproute2 / can-utils externally')
    ip = h.which('ip')
    rc, output = h.run([ip, '-details', '-json', 'link', 'show', 'type', 'vcan']) if ip else (1, '')
    try:
        links = json.loads(output) if rc == 0 else []
        interfaces = [link['ifname'] for link in links if link.get('linkinfo', {}).get('info_kind') == 'vcan']
    except (ValueError, TypeError, KeyError, AttributeError):
        interfaces = []
    add('vcan.interface', bool(interfaces),
        'Existing vcan: ' + ', '.join(interfaces) if interfaces else
        'No existing Linux vcan interface detected; doctor never loads modules or creates interfaces')
    rc, output = h.run(['modinfo', 'vcan']) if h.which('modinfo') else (1, '')
    add('vcan.module', rc == 0, 'vcan module metadata available (not a live CAN test)' if rc == 0 else
        'vcan module metadata unavailable; built-in support is possible; existing interface check is authoritative', required=False)

    # Check only operator-supplied external paths; no SDK discovery, download or execution.
    for name, variable, directory in [('sdk.host', 'QNX_HOST', True), ('sdk.target', 'QNX_TARGET', True),
                                      ('sdk.environment', 'CANOPY_QNX_ENV', False),
                                      ('qsti.image', 'CANOPY_QSTI_IMAGE', False)]:
        value = h.env.get(variable, '')
        passed = bool(value) and h.external(value, directory)
        add(name, passed, f'{variable}: external ' + ('directory' if directory else 'nonempty file') + ' present; contents/version unverified'
            if passed else f'Set {variable} to an existing external ' + ('directory' if directory else 'nonempty file') + '; never place SDK/images in this repository', scope='qnx-prerequisite')
    add('qnx.acceptance', False,
        'NOT RUN: QNX 8.0 guest boot, qcc/toolchain, mods-can.so load, PCI/CAN RX/TX, SLM, secpol and QPP acceptance remain unverified', scope='qnx-acceptance')
    ready = lambda scope: all(c['status'] == 'pass' for c in checks if c['required'] and c['scope'] == scope)
    return dict(schema_version=1, mode='x86_64-tcg-no-kvm-required',
                host_ready=ready('host'), qnx_prerequisites_ready=ready('qnx-prerequisite'),
                qnx_accepted=False, overall_ready=False, checks=checks,
                notice='Read-only availability/help probes only; no SDK execution, guest boot or target tests. No performance evidence.')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['doctor', 'up'])
    parser.add_argument('--json', action='store_true', help='machine-readable diagnostic report')
    args = parser.parse_args(argv)
    report = diagnose()
    if args.command == 'up':
        report['launch'] = 'BLOCKED: guest launcher is not implemented or validated; doctor availability does not authorize a QNX acceptance claim. No guest started.'
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print('CANopy doctor — x86_64 guest / TCG / no KVM required')
        for check in report['checks']:
            print(f"[{check['status'].upper()}] {check['scope']} / {check['id']}: {check['detail']}")
        print(f"Host preflight: {'READY' if report['host_ready'] else 'BLOCKED'}; QNX prerequisites: {'PRESENT (unverified)' if report['qnx_prerequisites_ready'] else 'BLOCKED'}; QNX acceptance: NOT RUN; overall: BLOCKED")
        print(report['notice'])
        if 'launch' in report:
            print(report['launch'])
    return 1


if __name__ == '__main__':
    sys.exit(main())
