"""Input generators for complexity analysis.

Each generator takes a size parameter n and returns input of that size
suitable for passing to the function under test.
"""

from __future__ import annotations

import random
import string
from typing import Any, Callable, Dict, List, Optional, Tuple


# Type alias for input generators
InputGenerator = Callable[[int], Any]


def gen_list(
    element_factory: Optional[Callable[[], Any]] = None,
    sorted_output: bool = False,
    reverse_sorted: bool = False,
) -> InputGenerator:
    """Generate a list of n elements.

    Args:
        element_factory: Callable that produces a single element.
            Defaults to random integers in [0, 10*n].
        sorted_output: If True, return the list sorted ascending.
        reverse_sorted: If True, return the list sorted descending.
    """

    def generator(n: int) -> List[Any]:
        if element_factory:
            result = [element_factory() for _ in range(n)]
        else:
            result = [random.randint(0, max(10 * n, 1)) for _ in range(n)]
        if sorted_output:
            result.sort()
        elif reverse_sorted:
            result.sort(reverse=True)
        return result

    return generator


def gen_string(alphabet: Optional[str] = None) -> InputGenerator:
    """Generate a random string of length n.

    Args:
        alphabet: Characters to choose from. Defaults to lowercase ASCII.
    """
    chars = alphabet or string.ascii_lowercase

    def generator(n: int) -> str:
        return "".join(random.choices(chars, k=n))

    return generator


def gen_int(max_scale: int = 1) -> InputGenerator:
    """Generate an integer proportional to n.

    Args:
        max_scale: Multiplier for the generated integer. Returns n * max_scale.
    """

    def generator(n: int) -> int:
        return n * max_scale

    return generator


def gen_graph(
    edge_density: float = 0.3,
    directed: bool = False,
) -> InputGenerator:
    """Generate an adjacency list graph with n nodes.

    Args:
        edge_density: Probability of edge between any two nodes (0-1).
        directed: If True, edges are one-directional.
    """

    def generator(n: int) -> Dict[int, List[int]]:
        graph: Dict[int, List[int]] = {i: [] for i in range(n)}
        for i in range(n):
            start = 0 if directed else i + 1
            for j in range(start, n):
                if i != j and random.random() < edge_density:
                    graph[i].append(j)
                    if not directed:
                        graph[j].append(i)
        return graph

    return generator


def gen_matrix(value_range: Tuple[int, int] = (0, 100)) -> InputGenerator:
    """Generate an n x n matrix (list of lists).

    Args:
        value_range: (min, max) range for random integer values.
    """
    lo, hi = value_range

    def generator(n: int) -> List[List[int]]:
        return [[random.randint(lo, hi) for _ in range(n)] for _ in range(n)]

    return generator


def gen_nested_dict(depth: int = 3) -> InputGenerator:
    """Generate a nested dictionary with n keys at each level.

    Args:
        depth: Number of nesting levels.
    """

    def _build(n: int, d: int) -> dict:
        if d <= 0:
            return {f"key_{i}": random.randint(0, 100) for i in range(n)}
        return {f"key_{i}": _build(n, d - 1) for i in range(n)}

    def generator(n: int) -> dict:
        return _build(n, depth)

    return generator
