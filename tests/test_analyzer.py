"""Tests for the analyzer module — integration tests with real functions."""

import pytest

from complexion.analyzer import ComplexityAnalyzer, analyze, compare
from complexion.generators import gen_list, gen_int, gen_string
from complexion.models import ComplexityClass


class TestAnalyzeRealFunctions:
    """Integration tests that analyze real functions and check results.

    These use small input sizes to keep tests fast.
    """

    def test_linear_search(self):
        """Linear search through a list is O(n)."""
        def linear_search(lst):
            target = -1  # Not in list
            for x in lst:
                if x == target:
                    return True
            return False

        result = analyze(
            linear_search, gen_list(),
            min_n=100, max_n=50000, num_points=6,
            measure_memory=False,
        )
        assert result.time_complexity in (
            ComplexityClass.O_N,
            ComplexityClass.O_N_LOG_N,  # Close to linear
        )
        assert result.time_confidence > 0.8

    def test_constant_time(self):
        """Dictionary lookup is O(1)."""
        cache = {i: i for i in range(100000)}

        def dict_lookup(n):
            return cache.get(42)

        result = analyze(
            dict_lookup, gen_int(),
            min_n=100, max_n=100000, num_points=6,
            measure_memory=False,
        )
        # O(1) functions are tricky due to noise; just check it's not O(n) or worse
        assert result.time_complexity.order <= ComplexityClass.O_N.order

    def test_sorted_builtin(self):
        """Python's sorted() is O(n log n)."""
        result = analyze(
            sorted, gen_list(),
            min_n=100, max_n=50000, num_points=6,
            measure_memory=False,
        )
        # sorted is O(n log n), but fitting may see O(n) for small sizes
        assert result.time_complexity.order <= ComplexityClass.O_N2.order

    def test_bubble_sort(self):
        """Bubble sort is O(n^2)."""
        def bubble_sort(lst):
            arr = list(lst)
            n = len(arr)
            for i in range(n):
                for j in range(0, n - i - 1):
                    if arr[j] > arr[j + 1]:
                        arr[j], arr[j + 1] = arr[j + 1], arr[j]
            return arr

        result = analyze(
            bubble_sort, gen_list(),
            min_n=50, max_n=2000, num_points=6,
            measure_memory=False,
        )
        assert result.time_complexity == ComplexityClass.O_N2
        assert result.time_confidence > 0.9


class TestCompare:
    def test_compare_two_sorts(self):
        """Compare built-in sort vs bubble sort."""
        def bubble_sort(lst):
            arr = list(lst)
            n = len(arr)
            for i in range(n):
                for j in range(0, n - i - 1):
                    if arr[j] > arr[j + 1]:
                        arr[j], arr[j + 1] = arr[j + 1], arr[j]
            return arr

        results = compare(
            {"sorted": sorted, "bubble": bubble_sort},
            gen_list(),
            min_n=50, max_n=2000, num_points=5,
        )
        assert len(results) == 2

        sorted_result = next(r for r in results if r.function_name == "sorted")
        bubble_result = next(r for r in results if r.function_name == "bubble")

        # Bubble sort should be detected as worse complexity
        assert bubble_result.time_complexity.order >= sorted_result.time_complexity.order


class TestComplexityAnalyzer:
    def test_custom_sizes(self):
        analyzer = ComplexityAnalyzer(sizes=[10, 50, 100])
        result = analyzer.analyze(sorted, gen_list())
        assert result.input_sizes == [10, 50, 100]

    def test_chart_output(self):
        analyzer = ComplexityAnalyzer(sizes=[10, 50, 100, 500])
        result = analyzer.analyze(sorted, gen_list(), name="my_sort")
        chart = analyzer.chart(result)
        assert "my_sort" in chart
        assert "n" in chart

    def test_fit_table_output(self):
        analyzer = ComplexityAnalyzer(sizes=[10, 50, 100, 500])
        result = analyzer.analyze(sorted, gen_list(), name="my_sort")
        table = analyzer.fit_table(result)
        assert "my_sort" in table
        assert "O(" in table

    def test_function_name_from_attribute(self):
        result = analyze(sorted, gen_list(), min_n=10, max_n=100, num_points=3)
        assert result.function_name == "sorted"
