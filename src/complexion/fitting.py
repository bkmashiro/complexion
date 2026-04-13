"""Statistical curve fitting for complexity determination.

Uses weighted nonlinear least-squares regression to fit measured data
against known complexity class growth functions.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from complexion.models import ComplexityClass, FitResult


def _safe_log(x: float) -> float:
    return math.log(max(x, 1e-300))


def fit_complexity(
    sizes: List[int],
    values: List[float],
    classes: Optional[List[ComplexityClass]] = None,
) -> List[FitResult]:
    """Fit measured values against complexity classes.

    Uses linear regression on the transformed model y = a*f(n) + b
    to find best-fit parameters, then ranks by goodness of fit.

    Args:
        sizes: Input sizes (n values).
        values: Measured values (time or memory) corresponding to each size.
        classes: Complexity classes to test. Defaults to all known classes.

    Returns:
        List of FitResult sorted by confidence (best first).
    """
    if classes is None:
        classes = list(ComplexityClass)

    if len(sizes) < 3:
        raise ValueError("Need at least 3 data points for fitting")

    if len(sizes) != len(values):
        raise ValueError("sizes and values must have the same length")

    results = []
    for cls in classes:
        result = _fit_single(sizes, values, cls)
        if result is not None:
            results.append(result)

    # Sort by AIC (lower is better), then by R-squared as tiebreaker
    results.sort(key=lambda r: (r.aic, -r.r_squared))

    # Re-rank: use a combined score that penalizes overly complex models
    # when simpler ones fit nearly as well
    if len(results) >= 2:
        results = _apply_parsimony(results)

    return results


def _fit_single(
    sizes: List[int],
    values: List[float],
    cls: ComplexityClass,
) -> Optional[FitResult]:
    """Fit data against a single complexity class using least squares.

    Model: y = a * f(n) + b
    This is a linear regression problem in the transformed space.
    """
    n = len(sizes)
    growth_fn = cls.growth_function

    # Compute f(n) for each data point
    try:
        f_values = [growth_fn(s, 1.0, 0.0) for s in sizes]
    except (OverflowError, ValueError):
        return None

    # Check for degenerate cases
    if any(math.isinf(f) or math.isnan(f) for f in f_values):
        return None

    # For O(1), f_values are all the same constant, so we just fit y = b
    if cls == ComplexityClass.O_1:
        mean_y = sum(values) / n
        ss_res = sum((y - mean_y) ** 2 for y in values)
        ss_tot = sum((y - mean_y) ** 2 for y in values)
        r_squared = 1.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot
        aic = _compute_aic(n, ss_res, 1)
        return FitResult(
            complexity=cls,
            r_squared=r_squared,
            coefficients=(0.0, mean_y),
            residual_sum=ss_res,
            aic=aic,
        )

    # Linear regression: y = a * f + b
    # Using normal equations
    sum_f = sum(f_values)
    sum_y = sum(values)
    sum_ff = sum(f * f for f in f_values)
    sum_fy = sum(f * y for f, y in zip(f_values, values))

    denom = n * sum_ff - sum_f * sum_f
    if abs(denom) < 1e-15:
        return None

    a = (n * sum_fy - sum_f * sum_y) / denom
    b = (sum_y - a * sum_f) / n

    # Compute R-squared
    mean_y = sum_y / n
    ss_tot = sum((y - mean_y) ** 2 for y in values)
    predictions = [a * f + b for f in f_values]
    ss_res = sum((y - p) ** 2 for y, p in zip(values, predictions))

    if ss_tot < 1e-15:
        r_squared = 1.0 if ss_res < 1e-15 else 0.0
    else:
        r_squared = 1.0 - ss_res / ss_tot

    # Penalize negative leading coefficient (growth should be non-negative)
    if a < -1e-10:
        r_squared = max(0.0, r_squared - 0.5)

    aic = _compute_aic(n, ss_res, 2)

    return FitResult(
        complexity=cls,
        r_squared=r_squared,
        coefficients=(a, b),
        residual_sum=ss_res,
        aic=aic,
    )


def _compute_aic(n: int, ss_res: float, k: int) -> float:
    """Compute Akaike Information Criterion.

    AIC = n * ln(SS_res / n) + 2k
    Lower is better. k is the number of parameters.
    """
    if n == 0:
        return float("inf")
    mse = ss_res / n
    if mse <= 0:
        return -float("inf")
    return n * _safe_log(mse) + 2 * k


def _apply_parsimony(results: List[FitResult]) -> List[FitResult]:
    """Apply Occam's razor: prefer simpler models when fit is comparable.

    If a simpler complexity class has R-squared within a threshold of
    a more complex class, prefer the simpler one.
    """
    THRESHOLD = 0.02  # R-squared difference threshold

    best = results[0]
    reordered = [best]

    remaining = results[1:]

    for result in remaining:
        # If this simpler model fits almost as well, promote it
        if (
            result.complexity.order < best.complexity.order
            and best.r_squared - result.r_squared < THRESHOLD
            and result.r_squared > 0.9
        ):
            reordered.insert(0, result)
            best = result
        else:
            reordered.append(result)

    return reordered
