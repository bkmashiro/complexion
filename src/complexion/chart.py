"""ASCII chart rendering for complexity analysis visualization."""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

from complexion.models import AnalysisResult, ComplexityClass, FitResult, Measurement


# Chart dimensions
DEFAULT_WIDTH = 60
DEFAULT_HEIGHT = 20


def render_measurements(
    result: AnalysisResult,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    show_fit: bool = True,
) -> str:
    """Render an ASCII chart of measurements with the best-fit curve.

    Args:
        result: The analysis result to visualize.
        width: Chart width in characters.
        height: Chart height in lines.
        show_fit: Whether to overlay the best-fit curve.

    Returns:
        Multi-line string containing the ASCII chart.
    """
    measurements = result.measurements
    if not measurements:
        return "(no data)"

    sizes = [m.n for m in measurements]
    times = [m.time_seconds for m in measurements]

    min_n, max_n = min(sizes), max(sizes)
    min_t, max_t = min(times), max(times)

    # Add some padding to ranges
    t_range = max_t - min_t
    if t_range < 1e-15:
        t_range = max_t if max_t > 0 else 1.0
        min_t = 0
        max_t = min_t + t_range

    n_range = max_n - min_n
    if n_range == 0:
        n_range = max_n if max_n > 0 else 1
        min_n = 0
        max_n = min_n + n_range

    # Build the grid
    grid = [[" " for _ in range(width)] for _ in range(height)]

    # Plot the best-fit curve if requested
    if show_fit and result.time_fits:
        best = result.best_time_fit
        fn = best.complexity.growth_function
        a, b = best.coefficients
        for col in range(width):
            n_val = min_n + (col / (width - 1)) * n_range
            try:
                predicted = fn(n_val, a, b)
                row = _value_to_row(predicted, min_t, max_t, height)
                if 0 <= row < height:
                    grid[row][col] = "·"
            except (OverflowError, ValueError):
                pass

    # Plot measured data points (overwrite fit curve)
    for m in measurements:
        col = _value_to_col(m.n, min_n, max_n, width)
        row = _value_to_row(m.time_seconds, min_t, max_t, height)
        if 0 <= row < height and 0 <= col < width:
            grid[row][col] = "●"

    # Build output with axes
    lines = []

    # Title
    best_label = result.time_complexity.value if result.time_fits else "?"
    confidence = result.time_confidence if result.time_fits else 0
    lines.append(
        f"  {result.function_name} — {best_label} "
        f"(confidence: {confidence:.0%})"
    )
    lines.append("")

    # Y-axis labels and grid
    for row_idx in range(height):
        t_val = max_t - (row_idx / (height - 1)) * t_range
        label = _format_time(t_val)
        line = f"{label:>10s} │{''.join(grid[row_idx])}"
        lines.append(line)

    # X-axis
    lines.append(f"{'':>10s} └{'─' * width}")

    # X-axis labels
    x_labels = f"{'':>11s}{min_n:<{width // 2}}{max_n:>{width - width // 2}}"
    lines.append(x_labels)
    lines.append(f"{'':>10s}  n →")

    return "\n".join(lines)


def render_comparison(
    results: List[AnalysisResult],
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> str:
    """Render a comparison chart of multiple functions.

    Args:
        results: List of analysis results to compare.
        width: Chart width in characters.
        height: Chart height in lines.

    Returns:
        Multi-line string containing the comparison chart.
    """
    if not results:
        return "(no data)"

    # Collect all data points
    all_sizes: List[int] = []
    all_times: List[float] = []
    for r in results:
        for m in r.measurements:
            all_sizes.append(m.n)
            all_times.append(m.time_seconds)

    min_n, max_n = min(all_sizes), max(all_sizes)
    min_t, max_t = min(all_times), max(all_times)
    t_range = max_t - min_t if max_t > min_t else max(max_t, 1e-9)
    n_range = max_n - min_n if max_n > min_n else max(max_n, 1)
    if t_range < 1e-15:
        min_t = 0
        t_range = max_t

    markers = "●○◆◇■□▲△"
    grid = [[" " for _ in range(width)] for _ in range(height)]

    # Plot each function
    legend_items = []
    for idx, r in enumerate(results):
        marker = markers[idx % len(markers)]
        legend_items.append(f"  {marker} {r.function_name} → {r.time_complexity.value}")
        for m in r.measurements:
            col = _value_to_col(m.n, min_n, max_n, width)
            row = _value_to_row(m.time_seconds, min_t, max_t, height)
            if 0 <= row < height and 0 <= col < width:
                grid[row][col] = marker

    lines = []
    lines.append("  Comparison")
    lines.append("")

    for row_idx in range(height):
        t_val = max_t - (row_idx / (height - 1)) * t_range
        label = _format_time(t_val)
        line = f"{label:>10s} │{''.join(grid[row_idx])}"
        lines.append(line)

    lines.append(f"{'':>10s} └{'─' * width}")
    x_labels = f"{'':>11s}{min_n:<{width // 2}}{max_n:>{width - width // 2}}"
    lines.append(x_labels)
    lines.append(f"{'':>10s}  n →")
    lines.append("")

    # Legend
    lines.append("  Legend:")
    for item in legend_items:
        lines.append(item)

    return "\n".join(lines)


def render_fit_table(result: AnalysisResult, top_n: int = 5) -> str:
    """Render a table of complexity fit results.

    Args:
        result: The analysis result.
        top_n: Number of top fits to show.

    Returns:
        Formatted table string.
    """
    lines = []
    lines.append(f"  Complexity Fits for: {result.function_name}")
    lines.append(f"  {'─' * 55}")
    lines.append(f"  {'Class':<14s} {'R²':>8s} {'AIC':>10s} {'Confidence':>12s}")
    lines.append(f"  {'─' * 55}")

    for fit in result.time_fits[:top_n]:
        bar = "█" * int(fit.confidence * 10) + "░" * (10 - int(fit.confidence * 10))
        lines.append(
            f"  {fit.complexity.value:<14s} {fit.r_squared:>8.4f} "
            f"{fit.aic:>10.1f} {bar} {fit.confidence:.1%}"
        )

    lines.append(f"  {'─' * 55}")

    if result.memory_fits:
        lines.append("")
        lines.append(f"  Memory Complexity: {result.best_memory_fit.complexity.value}")

    return "\n".join(lines)


def _value_to_row(value: float, min_val: float, max_val: float, height: int) -> int:
    """Map a value to a row index (top = max, bottom = min)."""
    if max_val == min_val:
        return height // 2
    normalized = (value - min_val) / (max_val - min_val)
    return height - 1 - int(round(normalized * (height - 1)))


def _value_to_col(value: float, min_val: float, max_val: float, width: int) -> int:
    """Map a value to a column index."""
    if max_val == min_val:
        return width // 2
    normalized = (value - min_val) / (max_val - min_val)
    return int(round(normalized * (width - 1)))


def _format_time(seconds: float) -> str:
    """Format a time value with appropriate units."""
    if seconds < 1e-6:
        return f"{seconds * 1e9:.0f}ns"
    elif seconds < 1e-3:
        return f"{seconds * 1e6:.1f}μs"
    elif seconds < 1:
        return f"{seconds * 1e3:.1f}ms"
    else:
        return f"{seconds:.2f}s"
