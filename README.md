# Complexion

**Empirical Algorithmic Complexity Analyzer**

Complexion determines the Big-O time and space complexity of any Python callable through empirical measurement and statistical curve fitting. Instead of manually analyzing code, you hand it a function and an input generator — it runs the function at increasing input sizes, measures performance, and fits the results against known complexity classes.

## Why This Matters

- **Verify theory**: confirm that your algorithm actually behaves as expected
- **Black-box analysis**: determine complexity of functions you can't read (C extensions, third-party code)
- **Catch regressions**: detect when a code change degrades algorithmic complexity in CI
- **Compare implementations**: see which of two approaches scales better, with charts

## Features

- Fits against 8 complexity classes: O(1), O(log n), O(√n), O(n), O(n log n), O(n²), O(n³), O(2ⁿ)
- Weighted least-squares regression with R² confidence scores and AIC model selection
- Memory profiling via `tracemalloc`
- ASCII charts showing growth curves with fit overlays
- Side-by-side comparison of multiple implementations
- Regression detection with JSON baselines for CI pipelines
- CLI and Python API
- Zero external dependencies (stdlib only)

## Install

```bash
# From the project directory
pip install -e .

# Or just add src/ to your PYTHONPATH
export PYTHONPATH=src:$PYTHONPATH
```

Requires Python 3.9+. No external dependencies.

## Quick Start

### Python API

```python
from complexion import analyze, compare, gen_list

# Analyze a single function
result = analyze(sorted, gen_list(), min_n=100, max_n=50000)
print(result.time_complexity.value)  # "O(n log n)"
print(result.time_confidence)        # 0.97

# Compare two implementations
results = compare(
    {"built-in sort": sorted, "bubble sort": bubble_sort},
    gen_list(),
    min_n=50,
    max_n=2000,
)
```

### CLI

```bash
# Analyze a function
complexion analyze mymodule:my_sort -g mymodule:gen_input

# Compare functions
complexion compare mymodule:sort_a mymodule:sort_b -g mymodule:gen_input

# Save a complexity baseline
complexion baseline save my_sort mymodule:my_sort -g mymodule:gen_input

# Check for regression in CI
complexion baseline check my_sort mymodule:my_sort -g mymodule:gen_input
```

### Regression Detection (CI)

```python
from complexion import analyze, gen_list
from complexion.regression import RegressionDetector

# In your test suite
detector = RegressionDetector(".complexion-baselines.json")
result = analyze(my_function, gen_list())
check = detector.check("my_function", result)
assert check.passed, check.message
```

## Input Generators

Complexion includes several built-in input generators:

| Generator | Description |
|-----------|-------------|
| `gen_list()` | Random integer lists |
| `gen_list(sorted_output=True)` | Pre-sorted lists |
| `gen_string()` | Random strings |
| `gen_int()` | Integers proportional to n |
| `gen_graph(edge_density=0.3)` | Adjacency-list graphs |
| `gen_matrix()` | n×n matrices |

Custom generators are just `Callable[[int], Any]`:

```python
def gen_binary_tree(n):
    """Generate a binary tree with n nodes."""
    return build_tree(range(n))

result = analyze(traverse, gen_binary_tree)
```

## Architecture

```
src/complexion/
├── __init__.py       # Public API exports
├── models.py         # Data models (ComplexityClass, FitResult, AnalysisResult)
├── generators.py     # Input generators (gen_list, gen_string, etc.)
├── measure.py        # Timing and memory measurement with outlier removal
├── fitting.py        # Statistical curve fitting (least squares, AIC, parsimony)
├── chart.py          # ASCII chart rendering
├── analyzer.py       # Main analyzer class and convenience functions
├── regression.py     # Baseline storage and regression detection
└── cli.py            # Command-line interface

tests/
├── test_models.py      # Unit tests for data models
├── test_generators.py  # Tests for input generators
├── test_fitting.py     # Tests for curve fitting (synthetic data)
├── test_measure.py     # Tests for timing/memory measurement
├── test_analyzer.py    # Integration tests with real algorithms
├── test_regression.py  # Tests for regression detection
├── test_chart.py       # Tests for chart rendering
└── test_cli.py         # Tests for CLI argument parsing

demo/
└── demo.py           # Runnable demo with sorting, searching, and comparison
```

## How It Works

1. **Measurement**: For each input size n, generate input via the generator, then time the function call. Uses multiple iterations with warm-up runs and IQR-based outlier removal for statistical robustness.

2. **Curve Fitting**: For each complexity class, fit the model `y = a·f(n) + b` using ordinary least squares. Compute R² (goodness of fit) and AIC (model selection criterion).

3. **Model Selection**: Rank candidates by AIC, then apply parsimony — if a simpler complexity class fits nearly as well as a more complex one (within 2% R²), prefer the simpler model.

4. **Regression Detection**: Compare the current best-fit complexity class against a stored baseline. Flag regressions when a function's complexity class worsens with sufficient confidence.

## Running the Demo

```bash
python demo/demo.py
```

This analyzes bubble sort, linear search, compares sorting algorithms, and demonstrates regression detection.

## Running Tests

```bash
cd /path/to/complexion
python -m pytest tests/ -v
```

## Seed Inspiration

This project was seeded by the numbers: 9227 6975 6151 2192 9263 8732 607 7285 3199 9216 7369 1561 3075 4254 6301 8311. The mix of primes (607, 6151, 9227), a perfect square (9216 = 96²), and composites with hidden structure inspired a tool that finds the hidden mathematical structure (complexity class) in empirical performance data — pattern recognition applied to algorithm analysis.

## License

MIT
