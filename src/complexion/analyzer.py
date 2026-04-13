"""Main analyzer module - the public API of complexion."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from complexion.chart import render_comparison, render_fit_table, render_measurements
from complexion.fitting import fit_complexity
from complexion.measure import generate_sizes, take_measurements
from complexion.models import AnalysisResult, ComplexityClass, FitResult, Measurement


class ComplexityAnalyzer:
    """Configurable complexity analyzer.

    Provides fine-grained control over analysis parameters.

    Example:
        analyzer = ComplexityAnalyzer(
            min_n=100,
            max_n=50000,
            num_points=10,
            measure_memory=True,
        )
        result = analyzer.analyze(my_sort, gen_list())
        print(result.summary())
        print(analyzer.chart(result))
    """

    def __init__(
        self,
        min_n: int = 10,
        max_n: int = 10000,
        num_points: int = 8,
        sizes: Optional[List[int]] = None,
        scale: str = "log",
        measure_memory: bool = True,
        max_seconds_per_size: float = 10.0,
        min_iterations: int = 3,
        classes: Optional[List[ComplexityClass]] = None,
    ):
        """Initialize the analyzer.

        Args:
            min_n: Minimum input size.
            max_n: Maximum input size.
            num_points: Number of input sizes to test.
            sizes: Explicit list of sizes (overrides min_n/max_n/num_points).
            scale: 'log' or 'linear' spacing for auto-generated sizes.
            measure_memory: Whether to measure memory usage.
            max_seconds_per_size: Time budget per input size.
            min_iterations: Minimum timing iterations per size.
            classes: Complexity classes to fit against.
        """
        self.sizes = sizes or generate_sizes(min_n, max_n, num_points, scale)
        self.measure_memory = measure_memory
        self.max_seconds_per_size = max_seconds_per_size
        self.min_iterations = min_iterations
        self.classes = classes

    def analyze(
        self,
        func: Callable,
        generator: Callable[[int], Any],
        name: Optional[str] = None,
    ) -> AnalysisResult:
        """Analyze the complexity of a function.

        Args:
            func: The function to analyze.
            generator: Input generator (takes int size, returns input).
            name: Display name for the function.

        Returns:
            AnalysisResult with complexity determination.
        """
        func_name = name or getattr(func, "__name__", str(func))

        measurements = take_measurements(
            func=func,
            generator=generator,
            sizes=self.sizes,
            measure_mem=self.measure_memory,
            max_seconds_per_size=self.max_seconds_per_size,
            min_iterations=self.min_iterations,
        )

        sizes = [m.n for m in measurements]
        times = [m.time_seconds for m in measurements]

        time_fits = fit_complexity(sizes, times, self.classes)

        memory_fits = None
        if self.measure_memory:
            mem_values = [m.memory_bytes for m in measurements]
            if all(v is not None for v in mem_values):
                memory_fits = fit_complexity(
                    sizes, [float(v) for v in mem_values], self.classes
                )

        return AnalysisResult(
            function_name=func_name,
            measurements=measurements,
            time_fits=time_fits,
            memory_fits=memory_fits,
            input_sizes=sizes,
        )

    def compare(
        self,
        funcs: Dict[str, Callable],
        generator: Callable[[int], Any],
    ) -> List[AnalysisResult]:
        """Compare multiple functions.

        Args:
            funcs: Dict mapping name to callable.
            generator: Shared input generator.

        Returns:
            List of AnalysisResults, one per function.
        """
        results = []
        for name, func in funcs.items():
            result = self.analyze(func, generator, name=name)
            results.append(result)
        return results

    @staticmethod
    def chart(result: AnalysisResult, **kwargs) -> str:
        """Render an ASCII chart of the analysis."""
        return render_measurements(result, **kwargs)

    @staticmethod
    def comparison_chart(results: List[AnalysisResult], **kwargs) -> str:
        """Render a comparison chart."""
        return render_comparison(results, **kwargs)

    @staticmethod
    def fit_table(result: AnalysisResult, **kwargs) -> str:
        """Render the fit results table."""
        return render_fit_table(result, **kwargs)


def analyze(
    func: Callable,
    generator: Callable[[int], Any],
    name: Optional[str] = None,
    min_n: int = 10,
    max_n: int = 10000,
    num_points: int = 8,
    measure_memory: bool = True,
) -> AnalysisResult:
    """Convenience function to analyze a single function.

    Args:
        func: The function to analyze.
        generator: Input generator (takes int size, returns input).
        name: Display name.
        min_n: Minimum input size.
        max_n: Maximum input size.
        num_points: Number of sizes to test.
        measure_memory: Whether to measure memory.

    Returns:
        AnalysisResult.

    Example:
        from complexion import analyze, gen_list

        result = analyze(sorted, gen_list())
        print(result.time_complexity.value)  # "O(n log n)"
    """
    analyzer = ComplexityAnalyzer(
        min_n=min_n,
        max_n=max_n,
        num_points=num_points,
        measure_memory=measure_memory,
    )
    return analyzer.analyze(func, generator, name=name)


def compare(
    funcs: Dict[str, Callable],
    generator: Callable[[int], Any],
    min_n: int = 10,
    max_n: int = 10000,
    num_points: int = 8,
) -> List[AnalysisResult]:
    """Convenience function to compare multiple functions.

    Args:
        funcs: Dict mapping name to callable.
        generator: Shared input generator.
        min_n: Minimum input size.
        max_n: Maximum input size.
        num_points: Number of sizes to test.

    Returns:
        List of AnalysisResults.
    """
    analyzer = ComplexityAnalyzer(
        min_n=min_n,
        max_n=max_n,
        num_points=num_points,
    )
    return analyzer.compare(funcs, generator)
