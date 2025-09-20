import random
import time
from typing import Callable, Optional

# Typing Simulator with human-like timing patterns
# - variable inter-key delays based on base CPS derived from WPM
# - short random pauses
# - occasional longer pauses after punctuation/newlines
# - bursts of faster typing for a few characters


class TypingSimulator:
    def __init__(
        self,
        text: str,
        wpm: int,
        send_char: Callable[[str], None],
        should_stop: Callable[[], bool],
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_done: Optional[Callable[[bool], None]] = None,
    ) -> None:
        self.text = text
        self.wpm = max(10, int(wpm))  # clamp minimal speed
        self.send_char = send_char
        self.should_stop = should_stop
        self.on_progress = on_progress
        self.on_done = on_done

        # Base characters per second, assuming 5 chars per word
        cps = (self.wpm * 5.0) / 60.0
        self.base_interval = 1.0 / cps  # seconds per character

        # Internal state for burst behavior
        self._burst_remaining = 0

    def _char_delay(self, idx: int, ch: str) -> float:
        # Baseline jitter
        if self._burst_remaining > 0:
            jitter_mult = random.uniform(0.55, 0.85)  # faster bursts
            self._burst_remaining -= 1
        else:
            jitter_mult = random.uniform(0.8, 1.4)

        delay = self.base_interval * jitter_mult

        # Chance to start a new burst occasionally
        if random.random() < 0.06 and self._burst_remaining == 0:
            self._burst_remaining = random.randint(3, 6)

        # Short pauses every so often
        if idx > 0 and idx % random.randint(7, 14) == 0:
            delay += random.uniform(0.18, 0.55)

        # Longer pauses after punctuation or newline occasionally
        if ch in ".,!?;:\n" and random.random() < 0.35:
            delay += random.uniform(0.4, 1.2)

        return max(0.001, delay)

    def run(self) -> bool:
        """Runs the simulator. Returns True if completed, False if stopped."""
        n = len(self.text)
        for i, ch in enumerate(self.text):
            if self.should_stop():
                if self.on_done:
                    self.on_done(False)
                return False

            # Map newline to Enter key in system-typing scenarios by sending \n;
            # it's up to the sender callable to interpret this.
            self.send_char(ch)

            if self.on_progress:
                try:
                    self.on_progress(i + 1, n)
                except Exception:
                    pass

            time.sleep(self._char_delay(i, ch))

        if self.on_done:
            try:
                self.on_done(True)
            except Exception:
                pass
        return True


def make_system_sender(controller) -> Callable[[str], None]:
    from pynput.keyboard import Key

    def _send(ch: str) -> None:
        if ch == "\n":
            controller.press(Key.enter)
            controller.release(Key.enter)
        else:
            controller.type(ch)
    return _send

