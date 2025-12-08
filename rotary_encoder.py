# rotary_encoder.py
import time
import digitalio

class RotaryEncoder:
    """
    Simplified + stable menu-friendly rotary encoder
    Provides:
        - update()
        - get_step() → returns -1 / +1 when rotated
    """

    def __init__(self, pin_a, pin_b, *, pull=digitalio.Pull.UP, debounce_ms=3):
        # A & B pins
        self._a = digitalio.DigitalInOut(pin_a)
        self._a.switch_to_input(pull=pull)

        self._b = digitalio.DigitalInOut(pin_b)
        self._b.switch_to_input(pull=pull)

        # timing
        self._debounce_ms = debounce_ms
        self._last_time = time.monotonic() * 1000

        # state
        self._last_state = (self._a.value, self._b.value)
        self._step = 0  # menu movement accumulator

    def update(self):
        """Call frequently. Detect and accumulate steps."""
        now = time.monotonic() * 1000
        raw = (self._a.value, self._b.value)

        # no change
        if raw == self._last_state:
            return

        # debounce
        if now - self._last_time < self._debounce_ms:
            return

        self._last_time = now

        prev = self._last_state
        self._last_state = raw

        # Decode quadrature
        a_prev, b_prev = prev
        a_now, b_now = raw

        # CLOCKWISE
        if a_prev == 1 and b_prev == 1 and a_now == 1 and b_now == 0:
            self._step += 1
        elif a_prev == 1 and b_prev == 0 and a_now == 0 and b_now == 0:
            self._step += 1
        elif a_prev == 0 and b_prev == 0 and a_now == 0 and b_now == 1:
            self._step += 1
        elif a_prev == 0 and b_prev == 1 and a_now == 1 and b_now == 1:
            self._step += 1

        # COUNTER CLOCKWISE
        elif a_prev == 1 and b_prev == 1 and a_now == 0 and b_now == 1:
            self._step -= 1
        elif a_prev == 0 and b_prev == 1 and a_now == 0 and b_now == 0:
            self._step -= 1
        elif a_prev == 0 and b_prev == 0 and a_now == 1 and b_now == 0:
            self._step -= 1
        elif a_prev == 1 and b_prev == 0 and a_now == 1 and b_now == 1:
            self._step -= 1

    def get_step(self):
        """Returns accumulated step: -1, +1, or 0."""
        step = self._step
        self._step = 0
        return step
