# rotary_encoder.py
# Simple quadrature rotary encoder helper for CircuitPython
#
# Usage:
#   from rotary_encoder import RotaryEncoder
#   encoder = RotaryEncoder(board.D3, board.D2, pulses_per_detent=1, debounce_ms=3)
#   ...
#   if encoder.update():
#       print(encoder.position)

import time
import digitalio


class RotaryEncoder:
    """
    Minimal rotary encoder reader for XIAO ESP32C3.
    - Uses two digital input pins (A, B)
    - Tracks .position as an integer count
    - .update() returns True if position changed since last call
    """

    def __init__(self, pin_a, pin_b, *, pulses_per_detent=1, debounce_ms=2):
        # Set up pins
        self._pin_a = digitalio.DigitalInOut(pin_a)
        self._pin_a.switch_to_input(pull=digitalio.Pull.UP)

        self._pin_b = digitalio.DigitalInOut(pin_b)
        self._pin_b.switch_to_input(pull=digitalio.Pull.UP)

        self.pulses_per_detent = max(1, int(pulses_per_detent))
        self._debounce_s = debounce_ms / 1000.0

        # State
        self.position = 0          # public position
        self._pulse_count = 0      # internal pulse accumulator
        self._last_state = self._read_state()
        self._last_time = time.monotonic()

    def _read_state(self):
        """Return current 2-bit state of the encoder: (A << 1) | B"""
        a = self._pin_a.value
        b = self._pin_b.value
        return (1 if a else 0) << 1 | (1 if b else 0)

    def update(self):
        """
        Poll the encoder.
        Returns True if a whole detent step was detected (position changed),
        otherwise False.
        """
        now = time.monotonic()
        if (now - self._last_time) < self._debounce_s:
            # too soon, skip reading
            return False

        state = self._read_state()
        if state == self._last_state:
            # no change
            return False

        # Quadrature lookup table: (prev_state, new_state) -> step
        step = _QUAD_STEP_TABLE.get((self._last_state, state), 0)

        self._last_state = state
        self._last_time = now

        if step == 0:
            return False

        # accumulate pulses, convert to detents
        self._pulse_count += step

        changed = False
        while self._pulse_count >= self.pulses_per_detent:
            self.position += 1
            self._pulse_count -= self.pulses_per_detent
            changed = True

        while self._pulse_count <= -self.pulses_per_detent:
            self.position -= 1
            self._pulse_count += self.pulses_per_detent
            changed = True

        return changed


# Standard quadrature state transition table
# States: 0b00, 0b01, 0b11, 0b10
# Valid transitions produce +1 or -1; anything else treated as 0 (noise)
_QUAD_STEP_TABLE = {
    # Clockwise
    (0b00, 0b01): +1,
    (0b01, 0b11): +1,
    (0b11, 0b10): +1,
    (0b10, 0b00): +1,
    # Counter-clockwise
    (0b00, 0b10): -1,
    (0b10, 0b11): -1,
    (0b11, 0b01): -1,
    (0b01, 0b00): -1,
}
