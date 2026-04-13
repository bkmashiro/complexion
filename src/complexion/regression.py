"""Complexity regression detection for CI/CD pipelines.

Compare current complexity against a known baseline and flag regressions
(e.g., an O(n) function that became O(n^2) after a code change).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from complexion.analyzer import ComplexityAnalyzer
from complexion.models import AnalysisResult, ComplexityClass


@dataclass
class BaselineEntry:
    """A stored complexity baseline for a function."""

    function_name: str
    time_complexity: str  # ComplexityClass.value
    time_confidence: float
    memory_complexity: Optional[str] = None
    memory_confidence: Optional[float] = None


@dataclass
class RegressionResult:
    """Result of a regression check."""

    function_name: str
    passed: bool
    baseline_complexity: str
    current_complexity: str
    baseline_confidence: float
    current_confidence: float
    severity: str  # "none", "warning", "regression"
    message: str


class RegressionDetector:
    """Detects complexity regressions by comparing against baselines.

    Usage:
        detector = RegressionDetector("baselines.json")

        # Generate baseline (run once)
        result = analyze(my_func, gen_list())
        detector.save_baseline("my_func", result)

        # Check for regression (run in CI)
        result = analyze(my_func, gen_list())
        check = detector.check("my_func", result)
        assert check.passed, check.message
    """

    def __init__(self, baseline_path: str = ".complexion-baselines.json"):
        self.baseline_path = Path(baseline_path)
        self._baselines: Dict[str, BaselineEntry] = {}
        self._load()

    def _load(self) -> None:
        """Load baselines from disk."""
        if self.baseline_path.exists():
            data = json.loads(self.baseline_path.read_text())
            for name, entry in data.items():
                self._baselines[name] = BaselineEntry(**entry)

    def _save(self) -> None:
        """Save baselines to disk."""
        data = {name: asdict(entry) for name, entry in self._baselines.items()}
        self.baseline_path.write_text(json.dumps(data, indent=2) + "\n")

    def save_baseline(self, name: str, result: AnalysisResult) -> None:
        """Save a complexity baseline for a function.

        Args:
            name: Identifier for the function.
            result: Analysis result to use as baseline.
        """
        entry = BaselineEntry(
            function_name=name,
            time_complexity=result.time_complexity.value,
            time_confidence=result.time_confidence,
        )
        if result.best_memory_fit:
            entry.memory_complexity = result.best_memory_fit.complexity.value
            entry.memory_confidence = result.best_memory_fit.confidence

        self._baselines[name] = entry
        self._save()

    def get_baseline(self, name: str) -> Optional[BaselineEntry]:
        """Get the stored baseline for a function."""
        return self._baselines.get(name)

    def check(
        self,
        name: str,
        result: AnalysisResult,
        confidence_threshold: float = 0.8,
    ) -> RegressionResult:
        """Check if a function's complexity has regressed from its baseline.

        Args:
            name: Function identifier (must match a stored baseline).
            result: Current analysis result.
            confidence_threshold: Minimum confidence to flag a regression.

        Returns:
            RegressionResult indicating pass/fail.
        """
        baseline = self._baselines.get(name)
        if baseline is None:
            return RegressionResult(
                function_name=name,
                passed=True,
                baseline_complexity="(none)",
                current_complexity=result.time_complexity.value,
                baseline_confidence=0.0,
                current_confidence=result.time_confidence,
                severity="none",
                message=f"No baseline found for '{name}'. Treating as pass.",
            )

        baseline_cls = _find_class(baseline.time_complexity)
        current_cls = result.time_complexity

        if baseline_cls is None:
            return RegressionResult(
                function_name=name,
                passed=True,
                baseline_complexity=baseline.time_complexity,
                current_complexity=current_cls.value,
                baseline_confidence=baseline.time_confidence,
                current_confidence=result.time_confidence,
                severity="none",
                message=f"Unknown baseline class '{baseline.time_complexity}'.",
            )

        # Compare complexity orders
        if current_cls.order > baseline_cls.order:
            if result.time_confidence >= confidence_threshold:
                severity = "regression"
                passed = False
                msg = (
                    f"REGRESSION: '{name}' changed from {baseline_cls.value} "
                    f"to {current_cls.value} (confidence: {result.time_confidence:.0%})"
                )
            else:
                severity = "warning"
                passed = True
                msg = (
                    f"WARNING: '{name}' might have regressed from {baseline_cls.value} "
                    f"to {current_cls.value}, but confidence is low "
                    f"({result.time_confidence:.0%})"
                )
        elif current_cls.order < baseline_cls.order:
            severity = "none"
            passed = True
            msg = (
                f"IMPROVED: '{name}' improved from {baseline_cls.value} "
                f"to {current_cls.value}"
            )
        else:
            severity = "none"
            passed = True
            msg = f"OK: '{name}' remains {current_cls.value}"

        return RegressionResult(
            function_name=name,
            passed=passed,
            baseline_complexity=baseline_cls.value,
            current_complexity=current_cls.value,
            baseline_confidence=baseline.time_confidence,
            current_confidence=result.time_confidence,
            severity=severity,
            message=msg,
        )

    def check_all(
        self,
        results: Dict[str, AnalysisResult],
        confidence_threshold: float = 0.8,
    ) -> List[RegressionResult]:
        """Check multiple functions against their baselines.

        Args:
            results: Dict mapping function names to analysis results.
            confidence_threshold: Minimum confidence for regression flags.

        Returns:
            List of RegressionResults.
        """
        return [
            self.check(name, result, confidence_threshold)
            for name, result in results.items()
        ]


def _find_class(value: str) -> Optional[ComplexityClass]:
    """Find a ComplexityClass by its value string."""
    for cls in ComplexityClass:
        if cls.value == value:
            return cls
    return None
