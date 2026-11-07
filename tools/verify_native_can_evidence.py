#!/usr/bin/env python3
"""Offline integrity recheck of private native libcan evidence (not a live test)."""
import json
from pathlib import Path
import sys
from native_can_three import parse_qnx, require_exact


def verify(directory):
    summary = json.loads((directory/'summary.json').read_text())
    if summary['pass'] is not True or len(summary['runs']) != 3:
        raise ValueError('incomplete/failed live series')
    if summary['sourceGate'] != 'libcan fallback acceptance ONLY; io-sock C2 NOT passed':
        raise ValueError('source qualification missing')
    for number in range(1, 4):
        base = directory/f'run{number}'
        def rows(suffix):
            return [tuple(row) for row in json.loads(base.with_suffix(suffix).read_text())]
        require_exact(rows('.rx-host.json'), parse_qnx(base.with_suffix('.rx-qnx.txt').read_text()))
        require_exact(rows('.tx-expected.json'), rows('.tx-host.json'))
        native = base.with_suffix('.serial.txt').read_text().replace('\r','').splitlines()
        if 'C2_TX_RC=0' not in native or 'C2_TX_END' not in native:
            raise ValueError('native TX completion missing')
        if json.loads(base.with_suffix('.result.json').read_text())['pass'] is not True:
            raise ValueError('failed run')
    return 'PASS: three recorded libcan runs byte-exact; offline recheck only'

if __name__ == '__main__':
    print(verify(Path(sys.argv[1])))
