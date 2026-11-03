import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from canopy_host.doctor import Host, ROOT, diagnose, main


class FakeHost:
    def __init__(self):
        self.env = {}
        self.missing = set()
        self.replies = {
            ('--version',): (0, 'QEMU emulator version 8.2.2'),
            ('-accel', 'help'): (0, 'Accelerators supported:\ntcg\n'),
            ('-device', 'help'): (0, 'name "edu"\nname "kvaser_pci"\n'),
            ('-device', 'edu,help'): (0, '  dma_mask=<uint64>\n'),
            ('-object', 'help'): (0, '  can-host-socketcan\n'),
        }
        self.calls = []
        self.links = '[{"ifname":"vcan0","linkinfo":{"info_kind":"vcan"}}]'
        self.binfmt = 'enabled\ninterpreter /usr/bin/qemu-x86_64-static\nflags: POCF\n'

    def which(self, name):
        return None if name in self.missing else '/usr/bin/' + name

    def exists(self, path):
        return False  # deliberately no KVM

    def read(self, path):
        return 'enabled\n' if path.endswith('/status') else self.binfmt

    def external(self, path, directory=False):
        return path.startswith('/external/')

    def run(self, argv):
        self.calls.append(argv)
        if 'qemu-x86_64' in argv[0] and 'system' not in argv[0]:
            return 0, 'qemu-x86_64 version 8.2.2'
        if argv[0].endswith('/ip'):
            return 0, self.links
        if argv[0] == 'modinfo':
            return 0, 'filename: vcan.ko'
        return self.replies[tuple(argv[1:])]


class DoctorTests(unittest.TestCase):
    def check(self, report, name):
        return next(c for c in report['checks'] if c['id'] == name)

    @patch('canopy_host.doctor.platform.machine', return_value='aarch64')
    def test_tcg_without_kvm_host_ready_but_sdk_and_acceptance_blocked(self, _):
        host = FakeHost()
        report = diagnose(host)
        self.assertTrue(report['host_ready'])
        self.assertFalse(report['qnx_prerequisites_ready'])
        self.assertFalse(report['overall_ready'])
        self.assertEqual(self.check(report, 'kvm')['status'], 'info')
        self.assertEqual(self.check(report, 'binfmt.x86_64')['status'], 'pass')
        self.assertEqual(sum(c[1:] == ['-device', 'help'] for c in host.calls), 1)
        self.assertTrue(all(c[0].split('/')[-1] in
                            ('qemu-system-x86_64', 'qemu-x86_64-static', 'ip', 'modinfo') for c in host.calls))

    def test_each_capability_missing_or_failed_blocks(self):
        for probe in [('-accel', 'help'), ('-device', 'help'),
                      ('-device', 'edu,help'), ('-object', 'help')]:
            for response in [(0, ''), (1, 'tcg name "edu" dma_mask= can-host-socketcan')]:
                host = FakeHost()
                host.replies[probe] = response
                self.assertFalse(diagnose(host)['host_ready'], (probe, response))

    def test_missing_qemu_and_can_utils_clean_diagnostics(self):
        host = FakeHost()
        host.missing.update(['qemu-system-x86_64', 'candump', 'cansend', 'cangen'])
        report = diagnose(host)
        self.assertFalse(report['host_ready'])
        self.assertEqual(self.check(report, 'qemu.version')['status'], 'blocked')
        self.assertEqual(self.check(report, 'tool.candump')['status'], 'blocked')

    @patch('canopy_host.doctor.platform.machine', return_value='aarch64')
    def test_user_emulator_missing_blocks_arm64(self, _):
        host = FakeHost()
        host.missing.update(['qemu-x86_64-static', 'qemu-x86_64'])
        self.assertFalse(diagnose(host)['host_ready'])

    def test_ubuntu_binfmt_interpreter_name(self):
        host = FakeHost()
        host.binfmt = 'enabled\ninterpreter /usr/libexec/qemu-binfmt/x86_64-binfmt-P\nflags: POF\n'
        self.assertEqual(self.check(diagnose(host), 'binfmt.x86_64')['status'], 'pass')

    def test_disabled_binfmt_is_advisory(self):
        host = FakeHost()
        host.binfmt = 'disabled\ninterpreter /usr/bin/qemu-x86_64-static\n'
        report = diagnose(host)
        self.assertEqual(self.check(report, 'binfmt.x86_64')['status'], 'info')
        self.assertTrue(report['host_ready'])

    def test_missing_malformed_or_nonvcan_interfaces(self):
        for links in ('[]', 'not json', '{}', 'null', '[{}]', '[{"ifname":"eth0"}]'):
            host = FakeHost()
            host.links = links
            self.assertFalse(diagnose(host)['host_ready'], links)

    def test_external_sdk_presence_never_implies_qnx_acceptance(self):
        host = FakeHost()
        host.env = {key: '/external/' + key for key in
                    ('QNX_HOST', 'QNX_TARGET', 'CANOPY_QNX_ENV', 'CANOPY_QSTI_IMAGE')}
        report = diagnose(host)
        self.assertTrue(report['qnx_prerequisites_ready'])
        self.assertFalse(report['qnx_accepted'])
        self.assertFalse(report['overall_ready'])

    def test_external_path_validation_rejects_repository_and_empty_files(self):
        host = Host()
        self.assertFalse(host.external(str(ROOT), directory=True))
        self.assertFalse(host.external(str(ROOT / 'README.md')))
        self.assertFalse(host.external('/nonexistent/canopy'))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'environment'
            path.touch()
            self.assertFalse(host.external(str(path)))
            path.write_text('mock environment, never sourced')
            self.assertTrue(host.external(str(path)))
            self.assertTrue(host.external(directory, directory=True))
            self.assertFalse(host.external(str(path), directory=True))

    def test_subprocess_timeout_and_missing_binary_are_clean(self):
        for error in (OSError('absent'), subprocess.TimeoutExpired(['qemu'], 5)):
            with patch('canopy_host.doctor.subprocess.run', side_effect=error):
                rc, message = Host().run(['qemu'])
                self.assertEqual(rc, 1)
                self.assertIn(message, ('OSError', 'TimeoutExpired'))

    def test_cli_json_and_up_never_launch(self):
        for command in ('doctor', 'up'):
            with patch('canopy_host.doctor.Host', return_value=FakeHost()), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main([command, '--json']), 1)
            report = json.loads(output.getvalue())
            self.assertFalse(report['overall_ready'])
            if command == 'up':
                self.assertIn('No guest started', report['launch'])

    def test_text_summary_distinguishes_host_from_target(self):
        with patch('canopy_host.doctor.Host', return_value=FakeHost()), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['doctor']), 1)
        self.assertIn('Host preflight: READY', output.getvalue())
        self.assertIn('QNX acceptance: NOT RUN; overall: BLOCKED', output.getvalue())
