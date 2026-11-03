"""Live host-only vcan fault runner. Never configures interfaces."""
import argparse
import json
from pathlib import Path
import signal
import subprocess
import sys
import time
from .runtime import SOURCE, emit


def rows(path):
    try:
        lines = Path(path).read_text().splitlines()
    except FileNotFoundError:
        return []
    result = []
    for line in lines:
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return result


def snapshot(path, obstacle=100, pilot=10):
    temporary = path.with_suffix('.new')
    temporary.write_text(json.dumps(dict(monotonic_ns=time.monotonic_ns(),
                                         obstacle_m=obstacle, pilot_speed_mps=pilot,
                                         source='host simulated sensors; NOT QNX')))
    temporary.replace(path)


def run_scenario(directory, scenario, interface='vcan0'):
    if scenario not in ('stale', 'obstacle', 'pilot', 'sigstop', 'kill', 'bad-crc', 'frozen'):
        raise ValueError('unknown scenario')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    inputs, fault = directory / 'inputs.json', directory / 'fault.txt'
    ecu_log, sender_log = directory / 'actuator.jsonl', directory / 'sender.jsonl'
    children, errors = [], []
    snapshot(inputs)
    with (directory / 'runner.jsonl').open('w') as stream:
        try:
            for role, output in [('actuator', ecu_log), ('sender', sender_log)]:
                command = [sys.executable, '-m', 'canopy_host.runtime', role,
                           '--interface', interface, '--duration', '9', '--output', str(output)]
                if role == 'sender':
                    command += ['--inputs', str(inputs), '--fault-file', str(fault)]
                error = (directory / (role + '.stderr')).open('w')
                errors.append(error)
                child = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=error)
                children.append(child)
                emit(stream, 'child-start', role=role, child_pid=child.pid)
                if role == 'actuator':
                    ready_deadline = time.monotonic() + 1
                    while not rows(ecu_log):
                        if child.poll() is not None or time.monotonic() >= ready_deadline:
                            raise RuntimeError('actuator failed readiness')
                        time.sleep(0.002)
            ecu, sender = children
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                snapshot(inputs)
                startup = rows(ecu_log)
                if any(r.get('accepted') and r.get('brake') == 0 for r in startup):
                    accepted = [r for r in startup if r.get('accepted')]
                    assert accepted[0]['recovery_cycles'] == 10
                    assert accepted[0]['brake'] == 100
                    assert startup[-1]['speed_mps'] > 1, 'startup clock consumed vehicle speed'
                    break
                if any(p.poll() is not None for p in children):
                    raise RuntimeError('runtime exited during startup')
                time.sleep(0.005)
            else:
                raise AssertionError('actuator never armed and released')
            fault_ns = time.monotonic_ns()
            emit(stream, 'fault', scenario=scenario, target_pid=sender.pid)
            if scenario in ('sigstop', 'kill'):
                sender.send_signal(signal.SIGSTOP if scenario == 'sigstop' else signal.SIGKILL)
            elif scenario in ('bad-crc', 'frozen'):
                fault.write_text(scenario)
            start = time.monotonic()
            agent_times = []
            while time.monotonic() - start < 2.9:
                if scenario != 'stale':
                    snapshot(inputs, obstacle=1 if scenario == 'obstacle' else 100,
                             pilot=30 if scenario == 'pilot' else 10)
                stamp = time.monotonic_ns()
                agent_times.append(stamp)
                emit(stream, 'host-agent', scenario=scenario,
                     sender_pid=sender.pid, actuator_pid=ecu.pid)
                time.sleep(0.02)
            after = [r for r in rows(ecu_log) if r['monotonic_ns'] >= fault_ns]
            samples = [r for r in after if r['event'] == 'actuator']
            assert samples and samples[-1]['speed_mps'] == 0, 'controlled stop not observed'
            assert samples[-1]['brake'] == 100 and samples[-1]['hazards']
            assert all(b['speed_mps'] <= a['speed_mps']
                       for a, b in zip(samples, samples[1:])), 'stop not monotonic'
            transitions = [r for r in after if r['event'] == 'watchdog-transition' and r['watchdog']]
            watchdog_elapsed = None
            if scenario in ('sigstop', 'kill', 'bad-crc', 'frozen'):
                assert transitions, 'independent watchdog did not expire'
                watchdog_elapsed = transitions[0]['elapsed_since_valid_ms']
                assert 100 <= watchdog_elapsed <= 150, watchdog_elapsed
            else:
                assert any(r.get('state') == 'SAFE_STOP' and r.get('latched')
                           for r in rows(sender_log) if r['monotonic_ns'] >= fault_ns)
            if scenario in ('bad-crc', 'frozen'):
                assert samples[-1]['rejected'] > 0
            max_agent_gap = max(b-a for a, b in zip(agent_times, agent_times[1:])) / 1e6
            assert max_agent_gap <= 100, max_agent_gap
            first_brake = next(r for r in samples if r['brake'] == 100)
            zero = next(r for r in samples if r['speed_mps'] == 0)
            result = dict(source=SOURCE, scenario=scenario, sender_pid=sender.pid,
                          actuator_pid=ecu.pid, watchdog_elapsed_ms=watchdog_elapsed,
                          fault_to_brake_ms=(first_brake['monotonic_ns']-fault_ns)/1e6,
                          fault_to_zero_ms=(zero['monotonic_ns']-fault_ns)/1e6,
                          host_agent_max_gap_ms=max_agent_gap, startup_recovery_cycles=10,
                          rejected=samples[-1]['rejected'], passed=True)
            emit(stream, 'result', **{k: v for k, v in result.items() if k != 'source'})
            (directory / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
            return result
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
            for child in children:
                child.wait(timeout=3)
            for error in errors:
                error.close()
            emit(stream, 'cleanup', child_returncodes=[p.returncode for p in children])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interface', default='vcan0')
    parser.add_argument('--output', required=True)
    parser.add_argument('--scenario', choices=['stale', 'obstacle', 'pilot', 'sigstop', 'kill',
                                             'bad-crc', 'frozen', 'all'], default='all')
    args = parser.parse_args()
    scenarios = ['stale', 'obstacle', 'pilot', 'sigstop', 'kill', 'bad-crc', 'frozen']
    for scenario in scenarios if args.scenario == 'all' else [args.scenario]:
        print(json.dumps(run_scenario(Path(args.output) / scenario, scenario, args.interface)), flush=True)


if __name__ == '__main__':
    main()
