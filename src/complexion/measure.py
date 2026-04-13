"""Performance measurement utilities.

Handles timing and memory profiling with statistical rigor:
warm-up runs, multiple iterations, outlier removal.
"""

from __future__ import annotations

import gc
import statistics
import sys
import time
import tracemalloc
from typing import Any, Callable, List, Optional, Tuple

from complexion.models import Measurement


def measure_time(
    func: Callable,
    input_data: Any,
    min_iterations: int = 3,
    max_seconds: float = 5.0,
    warmup: int = 1,
) -> Tuple[float, int]:
    """Measure the execution time of func(input_data).

    Runs the function multiple times and returns the median time.
    Automatically adjusts iteration count for very fast functions.

    Args:
        func: The function to measure.
        input_data: Input to pass to func.
        min_iterations: Minimum number of timed iterations.
        max_seconds: Maximum total time budget for measurement.
        warmup: Number of warm-up runs (not measured).

    Returns:
        Tuple of (median_time_seconds, iterations_run).
    """
    # Warm-up runs
    for _ in range(warmup):
        func(input_data)

    # First pass: see how long a single call takes
    gc.disable()
    try:
        start = time.perf_counter()
        func(input_data)
        single_time = time.perf_counter() - start
    finally:
        gc.enable()

    # Determine iteration count
    if single_time < 1e-6:
        # Very fast function: batch calls
        iterations = min(max(min_iterations, 1000), int(max_seconds / max(single_time, 1e-9)))
    elif single_time < 0.01:
        iterations = min(max(min_iterations, 100), int(max_seconds / single_time))
    elif single_time < 0.1:
        iterations = min(max(min_iterations, 10), int(max_seconds / single_time))
    else:
        iterations = max(min_iterations, min(5, int(max_seconds / single_time)))

    times: List[float] = []
    gc.disable()
    try:
        for _ in range(iterations):
            start = time.perf_counter()
            func(input_data)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
    finally:
        gc.enable()

    # Remove outliers (beyond 2 * IQR) if we have enough data
    if len(times) >= 5:
        times = _remove_outliers(times)

    median_time = statistics.median(times)
    return median_time, len(times)


def measure_memory(
    func: Callable,
    input_data: Any,
) -> Optional[int]:
    """Measure peak memory usage of func(input_data).

    Uses tracemalloc to measure memory allocated during the function call.

    Args:
        func: The function to measure.
        input_data: Input to pass to func.

    Returns:
        Peak memory usage in bytes, or None if measurement failed.
    """
    try:
        # Run once to warm up and stabilize allocations
        func(input_data)

        tracemalloc.start()
        try:
            # Take baseline snapshot
            snapshot_before = tracemalloc.take_snapshot()
            before_stats = snapshot_before.statistics("filename")
            before_total = sum(s.size for s in before_stats)

            func(input_data)

            snapshot_after = tracemalloc.take_snapshot()
            after_stats = snapshot_after.statistics("filename")
            after_total = sum(s.size for s in after_stats)

            # Peak during execution
            _, peak = tracemalloc.get_traced_memory()
            delta = max(0, after_total - before_total)

            # Use the larger of delta or peak as the estimate
            return max(delta, peak - before_total) if peak > before_total else delta
        finally:
            tracemalloc.stop()
    except Exception:
        return None


def take_measurements(
    func: Callable,
    generator: Callable[[int], Any],
    sizes: List[int],
    measure_mem: bool = True,
    max_seconds_per_size: float = 10.0,
    min_iterations: int = 3,
) -> List[Measurement]:
    """Take time (and optionally memory) measurements at given input sizes.

    Args:
        func: The function to measure.
        generator: Input generator that takes a size and returns input.
        sizes: List of input sizes to measure at.
        measure_mem: Whether to also measure memory usage.
        max_seconds_per_size: Time budget per size.
        min_iterations: Minimum timing iterations per size.

    Returns:
        List of Measurements, one per size.
    """
    results: List[Measurement] = []

    for n in sizes:
        input_data = generator(n)

        t, iters = measure_time(
            func,
            input_data,
            min_iterations=min_iterations,
            max_seconds=max_seconds_per_size,
        )

        mem = None
        if measure_mem:
            mem = measure_memory(func, input_data)

        results.append(
            Measurement(
                n=n,
                time_seconds=t,
                memory_bytes=mem,
                iterations=iters,
            )
        )

    return results


def _remove_outliers(data: List[float]) -> List[float]:
    """Remove outliers using the IQR method."""
    sorted_data = sorted(data)
    n = len(sorted_data)
    q1 = sorted_data[n // 4]
    q3 = sorted_data[3 * n // 4]
    iqr = q3 - q1
    lower = q1 - 2 * iqr
    upper = q3 + 2 * iqr
    filtered = [x for x in data if lower <= x <= upper]
    return filtered if len(filtered) >= 3 else data


def generate_sizes(
    min_n: int = 10,
    max_n: int = 10000,
    num_points: int = 8,
    scale: str = "log",
) -> List[int]:
    """Generate a sequence of input sizes for testing.

    Args:
        min_n: Smallest input size.
        max_n: Largest input size.
        num_points: Number of sizes to generate.
        scale: 'log' for logarithmic spacing, 'linear' for linear.

    Returns:
        List of integer input sizes.
    """
    import math

    if num_points < 2:
        return [min_n]

    if scale == "log":
        log_min = math.log(max(min_n, 1))
        log_max = math.log(max_n)
        step = (log_max - log_min) / (num_points - 1)
        sizes = [int(round(math.exp(log_min + i * step))) for i in range(num_points)]
    else:
        step = (max_n - min_n) / (num_points - 1)
        sizes = [int(round(min_n + i * step)) for i in range(num_points)]

    # Deduplicate and sort
    sizes = sorted(set(sizes))
    return sizes
