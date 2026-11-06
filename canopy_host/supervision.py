"""Original host policy/evidence gates. NOT a QNX supervisor or signal adapter."""
from collections import deque
from dataclasses import dataclass, field
import math
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass
class RestartBudget:
    """Five restarts per rolling 60s; sixth latches until explicit manual reset.

    Delays escalate across crashes, unlike SLM's failed-start-only backoff.
    Monotonic seconds; application policy, not QNX benchmark values.
    """
    attempts: deque = field(default_factory=deque)
    latched: bool = False
    last_time: float = -1.0

    def request(self, now):
        if (isinstance(now, bool) or not isinstance(now, (int, float)) or
                not math.isfinite(now) or now < self.last_time or now < 0):
            raise ValueError('finite nondecreasing monotonic time required')
        self.last_time = now
        if self.latched:
            return None
        while self.attempts and now - self.attempts[0] >= 60:
            self.attempts.popleft()
        if len(self.attempts) >= 5:
            self.latched = True
            return None
        self.attempts.append(now)
        return min(2 ** (len(self.attempts) - 1), 16)

    def manual_reset(self, *, driver_stopped, safestop_latched):
        if driver_stopped is not True or safestop_latched is not True:
            raise ValueError('reset requires stopped driver and latched safestop')
        self.attempts.clear()
        self.latched = False


def validate_slm(path):
    """Check our tiny config, NOT native parser compatibility."""
    data = Path(path).read_text()
    if '<!DOCTYPE' in data.upper() or '<!ENTITY' in data.upper():
        raise ValueError('entities forbidden')
    root = ET.fromstring(data)
    ns = '{urn:canopy:slm}'
    if root.tag != ns + 'system' or len(root) != 1:
        raise ValueError('one dedicated CAN component required')
    component = root[0]
    if component.tag != ns + 'component' or component.attrib != {'name': 'canopy-can'}:
        raise ValueError('unexpected component')
    expected = {
        'command': ('/proc/boot/dev-can-linux', {}),
        'args': ('-b id=0,freq=500k', {}),
        'repair': ('restart', {'backoff': '1'}),
        'stop': ('SIGTERM', {'stop': 'signal', 'child': 'false', 'timeout': '2000'}),
    }
    seen = set()
    for child in component:
        name = child.tag.removeprefix(ns)
        if name in seen or name not in expected or len(child):
            raise ValueError('unexpected/duplicate directive')
        seen.add(name)
        if ((child.text or '').strip(), child.attrib) != expected[name]:
            raise ValueError('unexpected command/repair policy')
    if seen != set(expected):
        raise ValueError('missing directive')
    return True


def validate_restart(record, *, require_qnx=False):
    """Validate evidence truth conditions, not authenticity. Never signals a PID.

    Native identity tokens require a reviewed target adapter (not Linux procfs).
    SSH continuity is independent of main PID continuity.
    """
    if require_qnx and record.get('source') != 'QNX native libcan fallback':
        raise ValueError('not native fallback evidence')
    def identity(key):
        value = record.get(key, {})
        if not isinstance(value, dict) or type(value.get('pid')) is not int or value['pid'] <= 1:
            raise ValueError('unsafe process PID')
        for name in ('instance', 'executable'):
            if not isinstance(value.get(name), str) or not value[name]:
                raise ValueError('missing identity')
        return value
    main, main_after = identity('main_before'), identity('main_after')
    before, after, killed = identity('can_before'), identity('can_after'), identity('killed')
    if main != main_after or killed != before or before['pid'] == after['pid']:
        raise ValueError('continuity/restart failed')
    if before['instance'] == after['instance'] or before['executable'] != after['executable']:
        raise ValueError('new CAN instance required')
    if main['pid'] in (before['pid'], after['pid']):
        raise ValueError('CAN must not be main process')
    if record.get('traffic_resumed') is not True or record.get('driver_ready') is not True:
        raise ValueError('PID-only restart insufficient')
    ssh = record.get('ssh', {})
    if not isinstance(ssh, dict):
        raise ValueError('invalid SSH evidence')
    continuous = (ssh.get('authenticated') is True and ssh.get('same_connection') is True
                  and ssh.get('continuous_probe') is True and
                  type(ssh.get('drops')) is int and ssh['drops'] == 0)
    if require_qnx and (before['executable'] != '/proc/boot/dev-can-linux' or
                        main['executable'] != '/sbin/io-sock'):
        raise ValueError('native executable provenance mismatch')
    return {'fallback_restart': True, 'ssh_uninterrupted': continuous,
            'full_c3': False, 'socketcan': False}
