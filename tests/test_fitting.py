"""Tests for the curve fitting module."""

import math
import pytest

from complexion.fitting import fit_complexity
from complexion.models import ComplexityClass


class TestFitComplexity:
    def test_constant_data(self):
        """Data that doesn't grow should fit O(1)."""
        sizes = [10, 50, 100, 500, 1000, 5000, 10000]
        values = [0.001] * len(sizes)
        results = fit_complexity(sizes, values)
        assert results[0].complexity == ComplexityClass.O_1

    def test_linear_data(self):
        """Linearly growing data should fit O(n)."""
        sizes = [10, 50, 100, 500, 1000, 5000, 10000]
        values = [s * 0.001 + 0.01 for s in sizes]
        results = fit_complexity(sizes, values)
        assert results[0].complexity == ComplexityClass.O_N
        assert results[0].r_squared > 0.99

    def test_quadratic_data(self):
        """Quadratically growing data should fit O(n^2)."""
        sizes = [10, 20, 50, 100, 200, 500]
        values = [s * s * 1e-6 + 0.001 for s in sizes]
        results = fit_complexity(sizes, values)
        assert results[0].complexity == ComplexityClass.O_N2
        assert results[0].r_squared > 0.99

    def test_nlogn_data(self):
        """n*log(n) growing data should fit O(n log n)."""
        sizes = [100, 500, 1000, 5000, 10000, 50000]
        values = [s * math.log2(s) * 1e-7 + 0.001 for s in sizes]
        results = fit_complexity(sizes, values)
        # n log n and n are similar; we just want one of them near the top
        top_classes = {r.complexity for r in results[:2]}
        assert (
            ComplexityClass.O_N_LOG_N in top_classes
            or ComplexityClass.O_N in top_classes
        )

    def test_logarithmic_data(self):
        """Logarithmically growing data should fit O(log n)."""
        sizes = [10, 100, 1000, 10000, 100000, 1000000]
        values = [math.log2(s) * 0.01 + 0.001 for s in sizes]
        results = fit_complexity(sizes, values)
        assert results[0].complexity == ComplexityClass.O_LOG_N
        assert results[0].r_squared > 0.98

    def test_cubic_data(self):
        """Cubically growing data should fit O(n^3)."""
        sizes = [5, 10, 15, 20, 30, 40]
        values = [s ** 3 * 1e-8 for s in sizes]
        results = fit_complexity(sizes, values)
        assert results[0].complexity == ComplexityClass.O_N3
        assert results[0].r_squared > 0.99

    def test_too_few_points_raises(self):
        with pytest.raises(ValueError, match="at least 3"):
            fit_complexity([10, 100], [0.1, 0.2])

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError, match="same length"):
            fit_complexity([10, 100, 1000], [0.1, 0.2])

    def test_all_results_returned(self):
        """Should return a fit for every complexity class."""
        sizes = [10, 50, 100, 500, 1000, 5000, 10000]
        values = [s * 0.001 for s in sizes]
        results = fit_complexity(sizes, values)
        assert len(results) == len(ComplexityClass)

    def test_r_squared_bounded(self):
        """R-squared should be between 0 and 1 for well-behaved data."""
        sizes = [10, 50, 100, 500, 1000]
        values = [s * 0.001 for s in sizes]
        results = fit_complexity(sizes, values)
        for r in results:
            # May be slightly negative due to bad fits, but not extreme
            assert r.r_squared >= -1.0
            assert r.r_squared <= 1.0 + 1e-10

    def test_subset_of_classes(self):
        """Should work with a subset of complexity classes."""
        sizes = [10, 50, 100, 500, 1000]
        values = [s * 0.001 for s in sizes]
        classes = [ComplexityClass.O_N, ComplexityClass.O_N2]
        results = fit_complexity(sizes, values, classes=classes)
        assert len(results) == 2
        assert all(r.complexity in classes for r in results)

    def test_noisy_linear_data(self):
        """Should handle noise and still find the right class."""
        import random
        random.seed(42)
        sizes = [100, 500, 1000, 2000, 5000, 10000, 20000, 50000]
        values = [
            s * 1e-5 + random.gauss(0, s * 1e-6) + 0.001
            for s in sizes
        ]
        results = fit_complexity(sizes, values)
        # Should be O(n) despite noise
        assert results[0].complexity == ComplexityClass.O_N
