"""Command-line interface for complexion.

Usage:
    python -m complexion analyze module:function --generator module:gen_func
    python -m complexion compare module:func1 module:func2 --generator module:gen
    python -m complexion baseline save func_name module:function --generator module:gen
    python -m complexion baseline check func_name module:function --generator module:gen
"""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Any, Callable, Optional

from complexion.analyzer import ComplexityAnalyzer
from complexion.chart import render_comparison, render_fit_table, render_measurements
from complexion.regression import RegressionDetector


def _import_callable(spec: str) -> Callable:
    """Import a callable from a 'module:attribute' specification."""
    if ":" not in spec:
        raise ValueError(
            f"Invalid callable spec '{spec}'. "
            f"Expected format: 'module:function' (e.g., 'mymodule:my_sort')"
        )
    module_path, attr_name = spec.rsplit(":", 1)

    # Add cwd to sys.path if not present
    if "" not in sys.path:
        sys.path.insert(0, "")

    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise ImportError(f"Cannot import module '{module_path}': {e}") from e

    if not hasattr(module, attr_name):
        raise AttributeError(f"Module '{module_path}' has no attribute '{attr_name}'")

    obj = getattr(module, attr_name)
    if not callable(obj):
        raise TypeError(f"'{spec}' is not callable")

    return obj


def cmd_analyze(args: argparse.Namespace) -> None:
    """Run the analyze command."""
    func = _import_callable(args.function)
    generator = _import_callable(args.generator)

    analyzer = ComplexityAnalyzer(
        min_n=args.min_n,
        max_n=args.max_n,
        num_points=args.points,
        measure_memory=not args.no_memory,
    )

    print(f"Analyzing {args.function}...")
    print(f"Input sizes: {analyzer.sizes}")
    print()

    result = analyzer.analyze(func, generator, name=args.function)

    print(result.summary())
    print()
    print(render_fit_table(result))
    print()
    print(render_measurements(result))


def cmd_compare(args: argparse.Namespace) -> None:
    """Run the compare command."""
    funcs = {}
    for spec in args.functions:
        func = _import_callable(spec)
        funcs[spec] = func

    generator = _import_callable(args.generator)

    analyzer = ComplexityAnalyzer(
        min_n=args.min_n,
        max_n=args.max_n,
        num_points=args.points,
        measure_memory=not args.no_memory,
    )

    print(f"Comparing {len(funcs)} functions...")
    print(f"Input sizes: {analyzer.sizes}")
    print()

    results = analyzer.compare(funcs, generator)

    for r in results:
        print(render_fit_table(r))
        print()

    print(render_comparison(results))

    # Summary
    print("\n  Summary:")
    for r in results:
        print(f"    {r.function_name}: {r.time_complexity.value} "
              f"(confidence: {r.time_confidence:.0%})")


def cmd_baseline_save(args: argparse.Namespace) -> None:
    """Save a complexity baseline."""
    func = _import_callable(args.function)
    generator = _import_callable(args.generator)

    analyzer = ComplexityAnalyzer(
        min_n=args.min_n,
        max_n=args.max_n,
        num_points=args.points,
    )

    print(f"Analyzing {args.name} for baseline...")
    result = analyzer.analyze(func, generator, name=args.name)

    detector = RegressionDetector(args.baseline_file)
    detector.save_baseline(args.name, result)

    print(f"Saved baseline: {result.time_complexity.value} "
          f"(confidence: {result.time_confidence:.0%})")
    print(f"Baseline file: {args.baseline_file}")


def cmd_baseline_check(args: argparse.Namespace) -> None:
    """Check for complexity regression."""
    func = _import_callable(args.function)
    generator = _import_callable(args.generator)

    analyzer = ComplexityAnalyzer(
        min_n=args.min_n,
        max_n=args.max_n,
        num_points=args.points,
    )

    print(f"Checking {args.name} for regression...")
    result = analyzer.analyze(func, generator, name=args.name)

    detector = RegressionDetector(args.baseline_file)
    check = detector.check(args.name, result, confidence_threshold=args.threshold)

    print(check.message)

    if not check.passed:
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="complexion",
        description="Empirical algorithmic complexity analyzer",
    )

    # Common arguments
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--min-n", type=int, default=10, help="Minimum input size")
    common.add_argument("--max-n", type=int, default=10000, help="Maximum input size")
    common.add_argument("--points", type=int, default=8, help="Number of data points")
    common.add_argument("--no-memory", action="store_true", help="Skip memory measurement")
    common.add_argument(
        "--generator", "-g", required=True,
        help="Input generator (module:function)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # analyze command
    p_analyze = subparsers.add_parser("analyze", parents=[common], help="Analyze a function")
    p_analyze.add_argument("function", help="Function to analyze (module:function)")
    p_analyze.set_defaults(handler=cmd_analyze)

    # compare command
    p_compare = subparsers.add_parser("compare", parents=[common], help="Compare functions")
    p_compare.add_argument("functions", nargs="+", help="Functions to compare")
    p_compare.set_defaults(handler=cmd_compare)

    # baseline commands
    baseline_common = argparse.ArgumentParser(add_help=False)
    baseline_common.add_argument(
        "--baseline-file", "-b", default=".complexion-baselines.json",
        help="Baseline file path",
    )

    p_baseline = subparsers.add_parser("baseline", help="Manage baselines")
    baseline_sub = p_baseline.add_subparsers(dest="baseline_command")

    p_save = baseline_sub.add_parser("save", parents=[common, baseline_common])
    p_save.add_argument("name", help="Baseline name")
    p_save.add_argument("function", help="Function (module:function)")
    p_save.set_defaults(handler=cmd_baseline_save)

    p_check = baseline_sub.add_parser("check", parents=[common, baseline_common])
    p_check.add_argument("name", help="Baseline name")
    p_check.add_argument("function", help="Function (module:function)")
    p_check.add_argument("--threshold", type=float, default=0.8, help="Confidence threshold")
    p_check.set_defaults(handler=cmd_baseline_check)

    return parser


def main(argv: Optional[list] = None) -> None:
    """Entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "handler"):
        parser.print_help()
        sys.exit(1)

    args.handler(args)


if __name__ == "__main__":
    main()
