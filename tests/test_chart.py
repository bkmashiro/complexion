"""Tests for the chart rendering module."""

import pytest

from complexion.chart import (
    render_comparison,
    render_fit_table,
    render_measurements,
    _format_time,
)
from complexion.models import (
    AnalysisResult,
    ComplexityClass,
    FitResult,
    Measurement,
)


def _make_result(name="test_func", num_points=5):
    measurements = [
        Measurement(n=10 * (i + 1), time_seconds=0.001 * (i + 1) ** 2)
        for i in range(num_points)
    ]
    fits = [
        FitResult(ComplexityClass.O_N2, 0.99, (1e-5, 0.0), 0.001, -50),
        FitResult(ComplexityClass.O_N, 0.70, (1e-3, 0.0), 0.5, -20),
    ]
    return AnalysisResult(
        function_name=name,
        measurements=measurements,
        time_fits=fits,
        input_sizes=[m.n for m in measurements],
    )


class TestRenderMeasurements:
    def test_basic_output(self):
        result = _make_result()
        chart = render_measurements(result)
        assert "test_func" in chart
        assert "O(n^2)" in chart
        assert "n" in chart

    def test_contains_axis_markers(self):
        result = _make_result()
        chart = render_measurements(result)
        assert "│" in chart
        assert "─" in chart
        assert "└" in chart

    def test_custom_dimensions(self):
        result = _make_result()
        chart = render_measurements(result, width=30, height=10)
        lines = chart.split("\n")
        # Should have title + blank + height lines + axis + labels + axis label
        assert len(lines) >= 10

    def test_empty_measurements(self):
        result = AnalysisResult(
            function_name="empty",
            measurements=[],
            time_fits=[],
        )
        chart = render_measurements(result)
        assert "no data" in chart

    def test_no_fit_overlay(self):
        result = _make_result()
        chart = render_measurements(result, show_fit=False)
        assert "test_func" in chart


class TestRenderComparison:
    def test_basic(self):
        r1 = _make_result("func_a")
        r2 = _make_result("func_b")
        chart = render_comparison([r1, r2])
        assert "Comparison" in chart
        assert "func_a" in chart
        assert "func_b" in chart
        assert "Legend" in chart

    def test_empty(self):
        chart = render_comparison([])
        assert "no data" in chart


class TestRenderFitTable:
    def test_basic(self):
        result = _make_result()
        table = render_fit_table(result)
        assert "O(n^2)" in table
        assert "O(n)" in table
        assert "R²" in table

    def test_top_n(self):
        result = _make_result()
        table = render_fit_table(result, top_n=1)
        # Should only show the best fit
        lines = [l for l in table.split("\n") if "O(" in l and "█" in l]
        assert len(lines) == 1


class TestFormatTime:
    def test_nanoseconds(self):
        assert "ns" in _format_time(1e-7)

    def test_microseconds(self):
        assert "μs" in _format_time(1e-4)

    def test_milliseconds(self):
        assert "ms" in _format_time(0.05)

    def test_seconds(self):
        assert "s" in _format_time(1.5)
