"""Tests for the models module."""

import math
import pytest

from complexion.models import (
    AnalysisResult,
    ComplexityClass,
    FitResult,
    Measurement,
)


class TestComplexityClass:
    def test_all_classes_have_growth_functions(self):
        for cls in ComplexityClass:
            fn = cls.growth_function
            assert callable(fn)
            # Should not raise for reasonable inputs
            result = fn(100, 1.0, 0.0)
            assert isinstance(result, (int, float))

    def test_growth_function_o1(self):
        fn = ComplexityClass.O_1.growth_function
        # O(1): constant regardless of n
        assert fn(1, 5.0, 0.0) == fn(1000, 5.0, 0.0)

    def test_growth_function_on(self):
        fn = ComplexityClass.O_N.growth_function
        # O(n): linear growth
        assert fn(100, 1.0, 0.0) == 100.0
        assert fn(200, 1.0, 0.0) == 200.0

    def test_growth_function_on2(self):
        fn = ComplexityClass.O_N2.growth_function
        assert fn(10, 1.0, 0.0) == 100.0
        assert fn(20, 1.0, 0.0) == 400.0

    def test_growth_function_o_log_n(self):
        fn = ComplexityClass.O_LOG_N.growth_function
        # log2(8) = 3
        assert abs(fn(8, 1.0, 0.0) - 3.0) < 1e-10

    def test_growth_function_o_n_log_n(self):
        fn = ComplexityClass.O_N_LOG_N.growth_function
        expected = 8 * math.log2(8)  # 8 * 3 = 24
        assert abs(fn(8, 1.0, 0.0) - expected) < 1e-10

    def test_growth_function_coefficients(self):
        fn = ComplexityClass.O_N.growth_function
        # y = a * n + b
        assert fn(100, 2.0, 5.0) == 205.0

    def test_order_property(self):
        orders = [cls.order for cls in ComplexityClass]
        # Orders should be unique and monotonically increasing
        assert len(set(orders)) == len(orders)
        assert orders == sorted(orders)

    def test_o1_is_fastest(self):
        assert ComplexityClass.O_1.order < ComplexityClass.O_N.order

    def test_o2n_is_slowest(self):
        assert ComplexityClass.O_2N.order > ComplexityClass.O_N3.order


class TestFitResult:
    def test_confidence_equals_r_squared(self):
        fit = FitResult(
            complexity=ComplexityClass.O_N,
            r_squared=0.95,
            coefficients=(1.0, 0.0),
            residual_sum=0.05,
            aic=-100,
        )
        assert fit.confidence == 0.95

    def test_confidence_clamps_to_zero(self):
        fit = FitResult(
            complexity=ComplexityClass.O_N,
            r_squared=-0.5,
            coefficients=(1.0, 0.0),
            residual_sum=100.0,
            aic=50,
        )
        assert fit.confidence == 0.0


class TestMeasurement:
    def test_basic_creation(self):
        m = Measurement(n=100, time_seconds=0.001)
        assert m.n == 100
        assert m.time_seconds == 0.001
        assert m.memory_bytes is None
        assert m.iterations == 1

    def test_with_memory(self):
        m = Measurement(n=100, time_seconds=0.001, memory_bytes=1024, iterations=10)
        assert m.memory_bytes == 1024
        assert m.iterations == 10


class TestAnalysisResult:
    def _make_result(self, fits=None, mem_fits=None):
        measurements = [
            Measurement(n=10, time_seconds=0.001),
            Measurement(n=100, time_seconds=0.01),
        ]
        if fits is None:
            fits = [
                FitResult(ComplexityClass.O_N, 0.99, (1e-4, 0.0), 0.001, -50),
                FitResult(ComplexityClass.O_N2, 0.80, (1e-6, 0.0), 0.1, -20),
            ]
        return AnalysisResult(
            function_name="test_func",
            measurements=measurements,
            time_fits=fits,
            memory_fits=mem_fits,
            input_sizes=[10, 100],
        )

    def test_best_time_fit(self):
        result = self._make_result()
        assert result.best_time_fit.complexity == ComplexityClass.O_N

    def test_time_complexity(self):
        result = self._make_result()
        assert result.time_complexity == ComplexityClass.O_N

    def test_time_confidence(self):
        result = self._make_result()
        assert result.time_confidence == 0.99

    def test_best_memory_fit_none(self):
        result = self._make_result()
        assert result.best_memory_fit is None

    def test_best_memory_fit(self):
        mem_fits = [
            FitResult(ComplexityClass.O_N, 0.98, (10.0, 0.0), 100, -30),
        ]
        result = self._make_result(mem_fits=mem_fits)
        assert result.best_memory_fit.complexity == ComplexityClass.O_N

    def test_summary(self):
        result = self._make_result()
        s = result.summary()
        assert "test_func" in s
        assert "O(n)" in s
        assert "99" in s  # confidence percentage
