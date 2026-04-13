"""Tests for the regression detection module."""

import json
import pytest
import tempfile
import os

from complexion.models import AnalysisResult, ComplexityClass, FitResult, Measurement
from complexion.regression import RegressionDetector, RegressionResult


def _make_result(complexity: ComplexityClass, confidence: float = 0.95) -> AnalysisResult:
    """Helper to create a mock AnalysisResult."""
    fits = [
        FitResult(
            complexity=complexity,
            r_squared=confidence,
            coefficients=(1.0, 0.0),
            residual_sum=0.01,
            aic=-50,
        )
    ]
    measurements = [
        Measurement(n=10, time_seconds=0.001),
        Measurement(n=100, time_seconds=0.01),
    ]
    return AnalysisResult(
        function_name="test_func",
        measurements=measurements,
        time_fits=fits,
        input_sizes=[10, 100],
    )


class TestRegressionDetector:
    def setup_method(self):
        self.tmpfile = tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        )
        self.tmpfile.write("{}")
        self.tmpfile.close()
        self.detector = RegressionDetector(self.tmpfile.name)

    def teardown_method(self):
        os.unlink(self.tmpfile.name)

    def test_save_and_load_baseline(self):
        result = _make_result(ComplexityClass.O_N)
        self.detector.save_baseline("my_func", result)

        # Create a new detector to test loading
        detector2 = RegressionDetector(self.tmpfile.name)
        baseline = detector2.get_baseline("my_func")
        assert baseline is not None
        assert baseline.time_complexity == "O(n)"
        assert baseline.time_confidence == 0.95

    def test_check_no_baseline(self):
        result = _make_result(ComplexityClass.O_N)
        check = self.detector.check("unknown_func", result)
        assert check.passed is True
        assert check.severity == "none"
        assert "No baseline" in check.message

    def test_check_no_regression(self):
        baseline_result = _make_result(ComplexityClass.O_N)
        self.detector.save_baseline("my_func", baseline_result)

        current = _make_result(ComplexityClass.O_N)
        check = self.detector.check("my_func", current)
        assert check.passed is True
        assert check.severity == "none"
        assert "OK" in check.message

    def test_check_regression_detected(self):
        baseline_result = _make_result(ComplexityClass.O_N)
        self.detector.save_baseline("my_func", baseline_result)

        # Now the function is O(n^2)
        current = _make_result(ComplexityClass.O_N2, confidence=0.95)
        check = self.detector.check("my_func", current)
        assert check.passed is False
        assert check.severity == "regression"
        assert "REGRESSION" in check.message

    def test_check_low_confidence_warning(self):
        baseline_result = _make_result(ComplexityClass.O_N)
        self.detector.save_baseline("my_func", baseline_result)

        current = _make_result(ComplexityClass.O_N2, confidence=0.5)
        check = self.detector.check("my_func", current)
        assert check.passed is True  # Low confidence = warning, not failure
        assert check.severity == "warning"
        assert "WARNING" in check.message

    def test_check_improvement(self):
        baseline_result = _make_result(ComplexityClass.O_N2)
        self.detector.save_baseline("my_func", baseline_result)

        current = _make_result(ComplexityClass.O_N)
        check = self.detector.check("my_func", current)
        assert check.passed is True
        assert "IMPROVED" in check.message

    def test_check_all(self):
        self.detector.save_baseline("func_a", _make_result(ComplexityClass.O_N))
        self.detector.save_baseline("func_b", _make_result(ComplexityClass.O_N))

        results = {
            "func_a": _make_result(ComplexityClass.O_N),
            "func_b": _make_result(ComplexityClass.O_N2),
        }
        checks = self.detector.check_all(results)
        assert len(checks) == 2
        assert checks[0].passed is True  # func_a: same
        assert checks[1].passed is False  # func_b: regression

    def test_baseline_file_persistence(self):
        """Baselines should persist across detector instances."""
        self.detector.save_baseline("func_x", _make_result(ComplexityClass.O_LOG_N))

        detector2 = RegressionDetector(self.tmpfile.name)
        baseline = detector2.get_baseline("func_x")
        assert baseline is not None
        assert baseline.time_complexity == "O(log n)"

    def test_custom_confidence_threshold(self):
        self.detector.save_baseline("my_func", _make_result(ComplexityClass.O_N))

        current = _make_result(ComplexityClass.O_N2, confidence=0.85)

        # With high threshold, 0.85 is below it -> warning
        check = self.detector.check("my_func", current, confidence_threshold=0.9)
        assert check.passed is True
        assert check.severity == "warning"

        # With lower threshold, 0.85 is above it -> regression
        check = self.detector.check("my_func", current, confidence_threshold=0.8)
        assert check.passed is False
        assert check.severity == "regression"
