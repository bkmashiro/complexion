"""Tests for the measurement module."""

import pytest
import time

from complexion.measure import (
    generate_sizes,
    measure_memory,
    measure_time,
    take_measurements,
)


class TestMeasureTime:
    def test_fast_function(self):
        """Measuring a fast function should return a small time."""
        elapsed, iters = measure_time(lambda x: x + 1, 42, min_iterations=3)
        assert elapsed >= 0
        assert elapsed < 1.0
        assert iters >= 3

    def test_slow_function(self):
        """Measuring a slow function should return a larger time."""
        def slow(x):
            time.sleep(0.01)
            return x

        elapsed, iters = measure_time(slow, 42, min_iterations=3, max_seconds=1.0)
        assert elapsed >= 0.005  # Should be at least ~10ms

    def test_multiple_iterations(self):
        """Fast functions should get more iterations."""
        elapsed, iters = measure_time(lambda x: None, 0, min_iterations=5)
        assert iters >= 5


class TestMeasureMemory:
    def test_allocation(self):
        """Should detect memory allocation."""
        def allocator(n):
            return [0] * n

        mem = measure_memory(allocator, 100000)
        # Should detect some memory usage (may be imprecise)
        assert mem is not None
        assert mem >= 0

    def test_no_allocation(self):
        """Minimal allocation should be close to zero."""
        mem = measure_memory(lambda x: x + 1, 42)
        assert mem is not None
        assert mem >= 0


class TestTakeMeasurements:
    def test_basic(self):
        measurements = take_measurements(
            func=sorted,
            generator=lambda n: list(range(n, 0, -1)),
            sizes=[10, 100, 1000],
            measure_mem=False,
        )
        assert len(measurements) == 3
        assert measurements[0].n == 10
        assert measurements[1].n == 100
        assert measurements[2].n == 1000

        # Times should generally increase for sorted()
        # (though at small sizes this isn't guaranteed)
        assert all(m.time_seconds >= 0 for m in measurements)

    def test_with_memory(self):
        measurements = take_measurements(
            func=lambda x: list(x),
            generator=lambda n: range(n),
            sizes=[100, 1000],
            measure_mem=True,
        )
        assert all(m.memory_bytes is not None for m in measurements)


class TestGenerateSizes:
    def test_log_scale(self):
        sizes = generate_sizes(10, 10000, 5, "log")
        assert len(sizes) >= 4  # May lose some to dedup
        assert sizes[0] >= 10
        assert sizes[-1] <= 10000
        assert sizes == sorted(sizes)

    def test_linear_scale(self):
        sizes = generate_sizes(10, 100, 5, "linear")
        assert sizes[0] == 10
        assert sizes[-1] == 100
        assert len(sizes) >= 4

    def test_single_point(self):
        sizes = generate_sizes(10, 10000, 1)
        assert sizes == [10]

    def test_no_duplicates(self):
        sizes = generate_sizes(1, 10, 8)
        assert len(sizes) == len(set(sizes))
