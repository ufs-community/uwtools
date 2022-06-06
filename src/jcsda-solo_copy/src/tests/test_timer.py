import time
from solo.timer import Timer


def test_timing():
    delay = 0.8
    with Timer() as t:
        time.sleep(delay)
        assert t.snapshot() - delay <= 0.1
        time.sleep(delay)
    assert t() - 2*delay <= 0.1
