"""Deterministic two-layer host model with explicit integer milliseconds."""
from dataclasses import dataclass
import math
from .protocol import Heartbeat, State


@dataclass(frozen=True)
class Inputs:
    speed_age_ms: int = 0
    obstacle_age_ms: int = 0
    obstacle_m: float = 100.0
    pilot_speed_mps: float = 0.0


class Safestop:
    """Only fresh sensor cycles release the latch; pilot has no clear API.

    One cycle per increasing timestamp. Recovery begins on fresh cycle ten,
    then reduces brake by ten percentage points per fresh cycle.
    """
    def __init__(self):
        self.latched = True
        self.fresh_cycles = 0
        self.brake = 100
        self.counter = 0
        self.last_ms = None

    def cycle(self, now_ms: int, inputs: Inputs) -> Heartbeat:
        if self.last_ms is not None and now_ms <= self.last_ms:
            raise ValueError('cycles require increasing time')
        gap = self.last_ms is not None and now_ms - self.last_ms > 20
        self.last_ms = now_ms
        healthy = (not gap and
                   0 <= inputs.speed_age_ms <= 30 and
                   0 <= inputs.obstacle_age_ms <= 30 and
                   math.isfinite(inputs.obstacle_m) and inputs.obstacle_m > 5 and
                   math.isfinite(inputs.pilot_speed_mps) and
                   0 <= inputs.pilot_speed_mps <= 20)
        if not healthy:
            self.latched, self.fresh_cycles, self.brake = True, 0, 100
        elif self.latched:
            self.fresh_cycles += 1
            if self.fresh_cycles >= 10:
                self.latched = False
        if self.latched:
            state = State.SAFE_STOP
        elif self.brake:
            state = State.RECOVER
            self.brake = max(0, self.brake - 10)
        else:
            state = State.DRIVE
        result = Heartbeat(state, self.brake, self.counter)
        self.counter = (self.counter + 1) & 15
        return result


class Actuator:
    """Independent watchdog. Rejected packets never refresh its deadline.

    Require exact +1 modulo-16; frozen, skipped, and backward counters reject.
    After timeout, retain the counter until ten healthy SAFE_STOP frames
    resynchronize (first non-repeated SAFE_STOP frame starts that sequence).
    A missing receiver scheduler tick cannot bypass timeout.
    """
    def __init__(self, speed_mps=10.0):
        if not math.isfinite(speed_mps) or speed_mps < 0:
            raise ValueError('invalid speed')
        self.speed_mps = speed_mps
        self.brake = 100
        self.hazards = True
        self.last_valid_ms = None
        self.counter = None
        self.timeout = True
        self.recovery_cycles = 0
        self.recovery_counter = None
        self.now_ms = 0
        self.rejected = 0

    def advance(self, now_ms):
        if now_ms < self.now_ms:
            raise ValueError('clock moved backwards')
        # Integrate only until deadline with old brake, then emergency brake.
        deadline = (self.last_valid_ms + 100
                    if self.last_valid_ms is not None else self.now_ms)
        before = max(0, min(now_ms, deadline) - self.now_ms)
        after = now_ms - self.now_ms - before
        self.speed_mps = max(0.0, self.speed_mps -
                             (before * self.brake / 100 + after) * 0.004)
        self.now_ms = now_ms
        if self.last_valid_ms is None or now_ms >= deadline:
            if not self.timeout:
                self.recovery_cycles = 0
                self.recovery_counter = None
            self.timeout = True
            self.brake, self.hazards = 100, True

    def receive(self, now_ms, can_id, payload):
        self.advance(now_ms)
        try:
            packet = Heartbeat.decode(can_id, payload)
        except (ValueError, TypeError):
            self.recovery_cycles = 0
            self.recovery_counter = None
            self.rejected += 1
            return False
        if self.timeout:
            previous = (self.recovery_counter if self.recovery_counter is not None
                        else self.counter)
            fresh = (previous is None or (packet.counter == (previous + 1) % 16
                     if self.recovery_counter is not None else packet.counter != previous))
            if packet.state != State.SAFE_STOP or not fresh:
                self.recovery_cycles = 0
                self.recovery_counter = None
                self.rejected += 1
                return False
            self.recovery_counter = packet.counter
            self.recovery_cycles += 1
            if self.recovery_cycles < 10:
                return False  # candidate, not accepted; watchdog remains asserted
            self.timeout = False
        elif packet.counter != (self.counter + 1) % 16:
            self.rejected += 1
            return False
        self.counter = packet.counter
        self.last_valid_ms = now_ms
        self.brake = packet.brake
        self.hazards = packet.state == State.SAFE_STOP
        return True
