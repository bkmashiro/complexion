"""Complexion - Empirical Algorithmic Complexity Analyzer.

Determine the Big-O time and space complexity of any callable
through empirical measurement and statistical curve fitting.
"""

__version__ = "0.1.0"

from complexion.analyzer import ComplexityAnalyzer, analyze, compare
from complexion.models import ComplexityClass, FitResult, AnalysisResult
from complexion.generators import InputGenerator, gen_list, gen_string, gen_int, gen_graph

__all__ = [
    "ComplexityAnalyzer",
    "analyze",
    "compare",
    "ComplexityClass",
    "FitResult",
    "AnalysisResult",
    "InputGenerator",
    "gen_list",
    "gen_string",
    "gen_int",
    "gen_graph",
]
