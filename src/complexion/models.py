"""Data models for complexity analysis results."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional, Tuple


class ComplexityClass(Enum):
    """Known algorithmic complexity classes."""

    O_1 = "O(1)"
    O_LOG_N = "O(log n)"
    O_SQRT_N = "O(sqrt(n))"
    O_N = "O(n)"
    O_N_LOG_N = "O(n log n)"
    O_N2 = "O(n^2)"
    O_N3 = "O(n^3)"
    O_2N = "O(2^n)"

    @property
    def growth_function(self) -> Callable[[float, float, float], float]:
        """Return the mathematical growth function for curve fitting.

        Each function takes (n, a, b) and returns the predicted time/space.
        Model: y = a * f(n) + b
        """
        funcs = {
            ComplexityClass.O_1: lambda n, a, b: a + b * 0,
            ComplexityClass.O_LOG_N: lambda n, a, b: a * math.log2(max(n, 1)) + b,
            ComplexityClass.O_SQRT_N: lambda n, a, b: a * math.sqrt(n) + b,
            ComplexityClass.O_N: lambda n, a, b: a * n + b,
            ComplexityClass.O_N_LOG_N: lambda n, a, b: a * n * math.log2(max(n, 1)) + b,
            ComplexityClass.O_N2: lambda n, a, b: a * n * n + b,
            ComplexityClass.O_N3: lambda n, a, b: a * n * n * n + b,
            ComplexityClass.O_2N: lambda n, a, b: a * (2.0 ** min(n, 40)) + b,
        }
        return funcs[self]

    @property
    def order(self) -> int:
        """Numeric ordering for comparison (lower = faster growth)."""
        ordering = {
            ComplexityClass.O_1: 0,
            ComplexityClass.O_LOG_N: 1,
            ComplexityClass.O_SQRT_N: 2,
            ComplexityClass.O_N: 3,
            ComplexityClass.O_N_LOG_N: 4,
            ComplexityClass.O_N2: 5,
            ComplexityClass.O_N3: 6,
            ComplexityClass.O_2N: 7,
        }
        return ordering[self]


@dataclass
class FitResult:
    """Result of fitting data against a single complexity class."""

    complexity: ComplexityClass
    r_squared: float  # Coefficient of determination (0-1, higher = better fit)
    coefficients: Tuple[float, float]  # (a, b) in y = a*f(n) + b
    residual_sum: float  # Sum of squared residuals
    aic: float  # Akaike Information Criterion (lower = better)

    @property
    def confidence(self) -> float:
        """Confidence score from 0 to 1 based on R-squared."""
        return max(0.0, self.r_squared)


@dataclass
class Measurement:
    """A single measurement at a given input size."""

    n: int
    time_seconds: float
    memory_bytes: Optional[int] = None
    iterations: int = 1


@dataclass
class AnalysisResult:
    """Complete result of a complexity analysis."""

    function_name: str
    measurements: List[Measurement]
    time_fits: List[FitResult]  # Sorted by confidence descending
    memory_fits: Optional[List[FitResult]] = None
    input_sizes: List[int] = field(default_factory=list)

    @property
    def best_time_fit(self) -> FitResult:
        """The most likely time complexity."""
        return self.time_fits[0]

    @property
    def best_memory_fit(self) -> Optional[FitResult]:
        """The most likely space complexity."""
        if self.memory_fits:
            return self.memory_fits[0]
        return None

    @property
    def time_complexity(self) -> ComplexityClass:
        """Shortcut for the best time complexity class."""
        return self.best_time_fit.complexity

    @property
    def time_confidence(self) -> float:
        """Confidence in the time complexity determination."""
        return self.best_time_fit.confidence

    def summary(self) -> str:
        """Human-readable summary of the analysis."""
        lines = [
            f"Function: {self.function_name}",
            f"Time complexity: {self.time_complexity.value} "
            f"(confidence: {self.time_confidence:.1%})",
        ]
        if self.best_memory_fit:
            lines.append(
                f"Space complexity: {self.best_memory_fit.complexity.value} "
                f"(confidence: {self.best_memory_fit.confidence:.1%})"
            )
        lines.append(f"Input sizes tested: {self.input_sizes}")
        return "\n".join(lines)
