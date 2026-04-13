#!/usr/bin/env python3
"""Complexion demo — analyze and compare sorting algorithms.

Run with: python demo/demo.py
"""

import sys
import os

# Add src to path for running without installation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from complexion import (
    ComplexityAnalyzer,
    analyze,
    compare,
    gen_list,
    gen_int,
    gen_string,
)
from complexion.chart import render_comparison, render_fit_table, render_measurements
from complexion.regression import RegressionDetector


# ──────────────────────────────────────────────────────────────────
# Demo functions with known complexities
# ──────────────────────────────────────────────────────────────────

def bubble_sort(lst):
    """O(n^2) sorting algorithm."""
    arr = list(lst)
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def linear_search(lst):
    """O(n) search - always scans the whole list."""
    target = -1  # never found
    for x in lst:
        if x == target:
            return True
    return False


def binary_search(lst):
    """O(log n) search on a sorted list."""
    arr = sorted(lst)  # Pre-sort (not counted in our measurement)
    target = -1
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def has_duplicate_quadratic(lst):
    """O(n^2) duplicate check using nested loops."""
    n = len(lst)
    for i in range(n):
        for j in range(i + 1, n):
            if lst[i] == lst[j]:
                return True
    return False


def has_duplicate_linear(lst):
    """O(n) duplicate check using a set."""
    seen = set()
    for x in lst:
        if x in seen:
            return True
        seen.add(x)
    return False


# ──────────────────────────────────────────────────────────────────
# Run the demo
# ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  COMPLEXION — Empirical Algorithmic Complexity Analyzer")
    print("=" * 70)
    print()

    # ── Demo 1: Analyze individual functions ───────────────────

    print("─" * 70)
    print("  Demo 1: Analyze bubble sort")
    print("─" * 70)
    print()

    result = analyze(
        bubble_sort,
        gen_list(),
        min_n=50,
        max_n=2000,
        num_points=7,
        measure_memory=False,
    )

    print(result.summary())
    print()
    print(render_fit_table(result))
    print()
    print(render_measurements(result))
    print()

    # ── Demo 2: Analyze linear search ──────────────────────────

    print("─" * 70)
    print("  Demo 2: Analyze linear search")
    print("─" * 70)
    print()

    result = analyze(
        linear_search,
        gen_list(),
        min_n=100,
        max_n=50000,
        num_points=7,
        measure_memory=False,
    )

    print(result.summary())
    print()
    print(render_fit_table(result))
    print()
    print(render_measurements(result))
    print()

    # ── Demo 3: Compare duplicate detection algorithms ─────────

    print("─" * 70)
    print("  Demo 3: Compare O(n) vs O(n^2) duplicate detection")
    print("─" * 70)
    print()

    # Use unique elements to force worst case for both
    results = compare(
        {
            "set-based (O(n))": has_duplicate_linear,
            "nested-loop (O(n^2))": has_duplicate_quadratic,
        },
        gen_list(),
        min_n=50,
        max_n=2000,
        num_points=6,
    )

    for r in results:
        print(render_fit_table(r))
        print()

    print(render_comparison(results))
    print()

    # ── Demo 4: Compare sorting algorithms ─────────────────────

    print("─" * 70)
    print("  Demo 4: Compare built-in sort vs bubble sort")
    print("─" * 70)
    print()

    results = compare(
        {
            "sorted() [O(n log n)]": sorted,
            "bubble_sort [O(n^2)]": bubble_sort,
        },
        gen_list(),
        min_n=50,
        max_n=2000,
        num_points=6,
    )

    for r in results:
        print(f"  {r.function_name}: {r.time_complexity.value} "
              f"(confidence: {r.time_confidence:.0%})")
    print()
    print(render_comparison(results))
    print()

    # ── Demo 5: Regression detection ───────────────────────────

    print("─" * 70)
    print("  Demo 5: Regression detection")
    print("─" * 70)
    print()

    import tempfile
    baseline_path = os.path.join(tempfile.gettempdir(), "complexion-demo-baselines.json")
    detector = RegressionDetector(baseline_path)

    # Save baseline as O(n)
    linear_result = analyze(
        has_duplicate_linear,
        gen_list(),
        min_n=100,
        max_n=50000,
        num_points=6,
        measure_memory=False,
    )
    detector.save_baseline("has_duplicate", linear_result)
    print(f"  Saved baseline: has_duplicate = {linear_result.time_complexity.value}")

    # Now check the O(n^2) version against it
    quad_result = analyze(
        has_duplicate_quadratic,
        gen_list(),
        min_n=50,
        max_n=2000,
        num_points=6,
        measure_memory=False,
    )
    check = detector.check("has_duplicate", quad_result)
    print(f"  Regression check: {check.message}")
    print(f"  Passed: {check.passed}")
    print()

    # Clean up
    try:
        os.unlink(baseline_path)
    except OSError:
        pass

    print("=" * 70)
    print("  Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
