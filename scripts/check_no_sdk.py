"""Conservative artifact hygiene; not a provenance or licensing guarantee."""
from pathlib import Path
import re
import subprocess
import sys

BAD_PART = re.compile(r'^(?:[.]sdk|sdk|qnxsdp.*|qnx[0-9]+|images|qnx-host|qnxsoftwarecenter.*|qsc|[.]qnx|[.]secrets)$', re.I)
BAD_EXT = re.compile(r'[.](?:ifs|img|qcow2?|vmdk|iso|o|a|so(?:[.].*)?|dll|exe|zip|tar|tgz|gz|xz|bz2|7z|deb|rpm|bin|run)$', re.I)
MARKERS = (b'QNX Software ' + b'Development Platform', b'QNX SDP ' + b'License',
           b'QNX_' + b'HOST=', b'QNX_' + b'TARGET=')


def problem(name, data, symlink=False):
    if any(BAD_PART.match(p) for p in Path(name).parts) or BAD_EXT.search(name):
        return 'SDK/image/archive/compiled artifact path'
    if symlink:
        return 'symlink cannot be audited'
    if len(data) > 2_000_000:
        return 'oversize artifact requires review'
    if bytes([0]) in data or data.startswith((bytes([127])+b'ELF', b'MZ', b'PK'+bytes([3,4]), b'QFI'+bytes([251]), bytes([31,139]))):
        return 'binary/archive content'
    if any(marker in data for marker in MARKERS):
        return 'SDK signature'
    return None


def main():
    root = Path.cwd()
    errors = []
    entries = subprocess.check_output(['git', 'ls-files', '--stage', '-z']).split(bytes([0]))
    for entry in filter(None, entries):
        meta, name = entry.split(bytes([9]), 1)
        mode, oid, stage = meta.split()
        name = name.decode('utf-8', 'surrogateescape')
        data = subprocess.check_output(['git', 'cat-file', 'blob', oid])
        issue = problem(name, data, mode == b'120000')
        if issue:
            errors.append(f'index:{name}: {issue}')
    for path in root.rglob('*'):
        relative = path.relative_to(root)
        if '.git' in relative.parts or '__pycache__' in relative.parts:
            continue
        if path.is_symlink():
            errors.append(f'worktree:{relative}: symlink')
        elif path.is_file():
            issue = problem(str(relative), path.read_bytes())
            if issue:
                errors.append(f'worktree:{relative}: {issue}')
    if errors:
        print(chr(10).join(sorted(set(errors))), file=sys.stderr)
        return 1
    print('PASS: staged blobs and worktree contain no recognized SDK/binary artifacts')
    return 0


if __name__ == '__main__':
    sys.exit(main())
