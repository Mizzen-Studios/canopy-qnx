"""Fail-closed host application budgets. No genuine target evidence accepted."""
from dataclasses import dataclass
import html
import json
import math
from pathlib import Path
import re

class EvidenceError(ValueError):
    """Malformed, unsupported or insufficient evidence."""

@dataclass(frozen=True)
class Budgets:
    deadline_ms: float
    restart_gap_ms: float
    overruns: int
    byte_exact: bool = True
    path: str = 'budgets.yaml'
    lines: tuple = (2, 3, 4, 5)

def _number(value, name, integer=False):
    try:
        valid = (not isinstance(value, bool) and isinstance(value, (int, float))
                 and math.isfinite(value) and value >= 0
                 and (not integer or isinstance(value, int)))
    except OverflowError:
        valid = False
    if not valid:
        raise EvidenceError(f'{name} must be a finite nonnegative number' + (' (integer)' if integer else ''))
    return value

def parse_budgets(text, path='budgets.yaml'):
    """Strict flat YAML subset: no aliases, tags, nesting, coercion or duplicates."""
    values, lines = {}, {}
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.split('#', 1)[0].rstrip()
        if not line:
            continue
        match = re.fullmatch(r'([a-z_]+): +([^\s]+)', line)
        if not match:
            raise EvidenceError(f'{path}:{line_no}: unsupported budget syntax')
        key, value = match.groups()
        if key in values:
            raise EvidenceError(f'{path}:{line_no}: duplicate key {key}')
        values[key], lines[key] = value, line_no
    keys = {'version', 'deadline_ms', 'restart_gap_ms', 'overruns', 'byte_exact'}
    if set(values) != keys:
        raise EvidenceError('budget keys must be exactly: ' + ', '.join(sorted(keys)))
    if values['version'] != '1' or values['byte_exact'] != 'true':
        raise EvidenceError('version must be 1 and byte_exact must be true')
    for key in ('deadline_ms', 'restart_gap_ms', 'overruns'):
        if not re.fullmatch(r'(0|[1-9][0-9]*)(\.[0-9]+)?', values[key]):
            raise EvidenceError(f'{key}: expected unsigned decimal')
    if '.' in values['overruns']:
        raise EvidenceError('overruns must be an integer')
    return Budgets(_number(float(values['deadline_ms']), 'deadline_ms'),
                   _number(float(values['restart_gap_ms']), 'restart_gap_ms'),
                   _number(int(values['overruns']), 'overruns', True), True, str(path),
                   tuple(lines[k] for k in ('deadline_ms', 'restart_gap_ms', 'overruns', 'byte_exact')))

def load_budgets(path='budgets.yaml'):
    return parse_budgets(Path(path).read_text(encoding='utf-8'), str(path))

@dataclass(frozen=True)
class Frame:
    can_id: int
    extended: bool
    dlc: int
    payload: bytes
    remote: bool = False

def parse_candump(text):
    """Classic candump -L/human output. Preserve ID type, RTR, DLC, bytes/order.

    Ignore timestamps/interfaces only. Reject unsupported FD/error frames and
    malformed lines rather than silently dropping any part of a capture.
    """
    frames = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        line = re.sub(r'^\s*\([0-9]+(?:\.[0-9]+)?\)\s*', '', raw).strip()
        compact = re.fullmatch(r'\S+\s+([0-9A-Fa-f]{3}|[0-9A-Fa-f]{8})#([0-9A-Fa-f]*|R[0-8]?)', line)
        human = re.fullmatch(r'\S+\s+([0-9A-Fa-f]{3}|[0-9A-Fa-f]{8})\s+\[([0-8])\]\s*(.*?)\s*', line)
        if compact:
            ident, data = compact.groups()
            remote = data.startswith('R')
            dlc = int(data[1:] or '0') if remote else len(data) // 2
            if not remote and len(data) % 2:
                raise EvidenceError(f'candump:{line_no}: odd payload length')
            payload = b'' if remote else bytes.fromhex(data)
        elif human:
            ident, size, data = human.groups()
            dlc = int(size)
            remote = data == 'remote request'
            if not remote and not re.fullmatch(r'(?:[0-9A-Fa-f]{2}(?: +[0-9A-Fa-f]{2})*)?', data):
                raise EvidenceError(f'candump:{line_no}: invalid payload')
            payload = b'' if remote else bytes.fromhex(data)
        else:
            raise EvidenceError(f'candump:{line_no}: unsupported or malformed frame')
        extended = len(ident) == 8
        can_id = int(ident, 16)
        if can_id > (0x1fffffff if extended else 0x7ff) or dlc > 8 or (not remote and len(payload) != dlc):
            raise EvidenceError(f'candump:{line_no}: ID/DLC/payload inconsistent')
        frames.append(Frame(can_id, extended, dlc, payload, remote))
    if not frames:
        raise EvidenceError('candump: insufficient evidence (empty log)')
    return tuple(frames)

def compare_candump(expected, actual):
    """Return first mismatch details, or None. Order/count must match exactly."""
    left, right = parse_candump(expected), parse_candump(actual)
    for index, (a, b) in enumerate(zip(left, right), 1):
        if a != b:
            return f'frame {index}: expected {a!r}; observed {b!r} (order is significant)'
    if len(left) != len(right):
        return f'frame count: expected {len(left)}; observed {len(right)} (missing/extra frames)'
    return None

@dataclass(frozen=True)
class CheckResult:
    code: str
    status: str
    message: str
    observed: str
    budget: str
    path: str
    line: int

@dataclass(frozen=True)
class Report:
    source: str
    results: tuple
    restart_chain: tuple = ()
    target_evidence: str = 'none'

    @property
    def passed(self):
        return bool(self.results) and all(item.status == 'pass' for item in self.results)

    @property
    def exit_code(self):
        return 0 if self.passed else 1

def _validate_finite_tree(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise EvidenceError('nonfinite value anywhere in evidence is forbidden')
    if isinstance(value, dict):
        for child in value.values():
            _validate_finite_tree(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _validate_finite_tree(child)

def load_evidence(path):
    def reject(value):
        raise EvidenceError(f'nonfinite JSON value: {value}')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise EvidenceError(f'duplicate evidence key: {key}')
            result[key] = value
        return result
    try:
        result = json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=reject, object_pairs_hook=pairs)
        _validate_finite_tree(result)
        return result
    except (ValueError, OSError) as exc:
        raise EvidenceError(str(exc)) from exc

def check(budgets, evidence):
    """Check all four gates; absent observations fail rather than pass vacuously."""
    if not isinstance(budgets, Budgets):
        raise EvidenceError('expected validated Budgets')
    for name in ('deadline_ms', 'restart_gap_ms', 'overruns'):
        _number(getattr(budgets, name), name, name == 'overruns')
    if budgets.byte_exact is not True:
        raise EvidenceError('byte_exact cannot be disabled')
    codes = ('CP101', 'CP102', 'CP103', 'CP104')
    messages = ('deadline', 'restart gap', 'overrun count', 'byte-exact frames')
    limits = (f'{budgets.deadline_ms:g} ms', f'{budgets.restart_gap_ms:g} ms', str(budgets.overruns), 'identical ordered frames')
    results, chain = [], ()
    source = evidence.get('source', 'UNKNOWN') if isinstance(evidence, dict) else 'UNKNOWN'
    provenance_ok = (isinstance(evidence, dict) and source in ('HOST SIM', 'HOST VCAN')
                     and evidence.get('target_evidence') == 'none'
                     and type(evidence.get('version')) is int and evidence['version'] == 1)
    try:
        _validate_finite_tree(evidence)
    except EvidenceError:
        provenance_ok = False
    for i, code in enumerate(codes):
        try:
            if not provenance_ok:
                raise EvidenceError('require version 1, HOST SIM/HOST VCAN and target_evidence none')
            if i == 0:
                samples = evidence['deadline_samples_ms']
                if not isinstance(samples, list) or not samples:
                    raise EvidenceError('nonempty deadline_samples_ms required')
                observed = max(_number(v, 'deadline sample') for v in samples)
                passed = observed <= budgets.deadline_ms
                detail = f'{observed:g} ms (maximum of {len(samples)} samples)'
            elif i == 1:
                hops = evidence['restart_chain_ms']
                names = ('death_to_spawn', 'driver_up', 'ifconfig', 'canvss', 'first_frame')
                if not isinstance(hops, dict) or set(hops) != set(names):
                    raise EvidenceError('all five restart hops required')
                chain = tuple((name, _number(hops[name], name)) for name in names)
                observed = _number(sum(value for _, value in chain), 'restart total')
                passed, detail = observed <= budgets.restart_gap_ms, f'{observed:g} ms'
            elif i == 2:
                observed = _number(evidence['overruns'], 'overruns', True)
                passed, detail = observed <= budgets.overruns, str(observed)
            else:
                detail = compare_candump(evidence['expected_candump'], evidence['actual_candump'])
                passed = detail is None
                detail = detail or 'identical ordered frames'
            results.append(CheckResult(code, 'pass' if passed else 'fail', messages[i], detail, limits[i], budgets.path, budgets.lines[i]))
        except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
            results.append(CheckResult(code, 'fail', messages[i], f'insufficient/invalid evidence: {exc}', limits[i], budgets.path, budgets.lines[i]))
    return Report(source if provenance_ok else 'UNKNOWN (invalid provenance)', tuple(results), chain)

def render_rustc(report):
    lines = [f'source: {report.source}; target evidence: none; host app budgets, NOT QNX measurements']
    for item in report.results:
        lines.extend([f'{"ok" if item.status == "pass" else "error"}[{item.code}]: {item.message}',
                      f'  --> {item.path}:{item.line}', f'   = observed: {item.observed}', f'   = budget: {item.budget}'])
    if report.restart_chain:
        lines.append('   = chain: ' + ' -> '.join(f'{name} {value:g} ms' for name, value in report.restart_chain))
    lines.append('SDK driver FI/bus-off/error-passive/overrun flood gate: BLOCKED; no target evidence')
    return '\n'.join(lines) + '\n'

def _escape_annotation(value, property=False):
    value = str(value).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
    return value.replace(':', '%3A').replace(',', '%2C') if property else value

def render_github_annotations(report):
    return '\n'.join(f'::error file={_escape_annotation(r.path, True)},line={r.line},title={r.code}::{_escape_annotation(r.message + ": " + r.observed)}'
                     for r in report.results if r.status != 'pass')

def render_github_summary(report):
    def cell(value):
        return html.escape(str(value)).replace('|', '&#124;').replace('\r', ' ').replace('\n', '<br>').replace(chr(96), '&#96;')
    rows = ['## CANopy host application budgets',
            f'Source: **{cell(report.source)}**; target evidence: **none**. Not QNX measurements.',
            '', '| Code | Result | Check | Observed | Budget |', '|---|---|---|---|---|']
    rows += [f'| {r.code} | {r.status.upper()} | {cell(r.message)} | {cell(r.observed)} | {cell(r.budget)} |' for r in report.results]
    if report.restart_chain:
        rows += ['', chr(96)*3 + 'mermaid', 'flowchart LR']
        for i, (name, value) in enumerate(report.restart_chain):
            rows.append(f'  n{i}["{name}: {value:g} ms"]' + (f' --> n{i+1}' if i < len(report.restart_chain)-1 else ''))
        rows.append(chr(96)*3)
    rows += ['', '**BLOCKED:** SDK driver FI (bus-off/error-passive) and target overrun flood; no genuine target evidence.', '']
    return '\n'.join(rows)
