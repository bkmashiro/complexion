"""Tests for the generators module."""

import pytest

from complexion.generators import (
    gen_graph,
    gen_int,
    gen_list,
    gen_matrix,
    gen_nested_dict,
    gen_string,
)


class TestGenList:
    def test_basic(self):
        g = gen_list()
        result = g(100)
        assert len(result) == 100
        assert all(isinstance(x, int) for x in result)

    def test_sorted(self):
        g = gen_list(sorted_output=True)
        result = g(50)
        assert result == sorted(result)

    def test_reverse_sorted(self):
        g = gen_list(reverse_sorted=True)
        result = g(50)
        assert result == sorted(result, reverse=True)

    def test_custom_factory(self):
        g = gen_list(element_factory=lambda: "x")
        result = g(10)
        assert all(x == "x" for x in result)

    def test_zero_size(self):
        g = gen_list()
        result = g(0)
        assert result == []


class TestGenString:
    def test_basic(self):
        g = gen_string()
        result = g(50)
        assert len(result) == 50
        assert isinstance(result, str)

    def test_custom_alphabet(self):
        g = gen_string(alphabet="ab")
        result = g(100)
        assert all(c in "ab" for c in result)


class TestGenInt:
    def test_basic(self):
        g = gen_int()
        assert g(100) == 100

    def test_scaled(self):
        g = gen_int(max_scale=10)
        assert g(5) == 50


class TestGenGraph:
    def test_basic(self):
        g = gen_graph(edge_density=0.5)
        result = g(10)
        assert len(result) == 10
        assert all(isinstance(v, list) for v in result.values())

    def test_undirected_symmetry(self):
        g = gen_graph(edge_density=1.0, directed=False)
        result = g(5)
        for node, neighbors in result.items():
            for neighbor in neighbors:
                assert node in result[neighbor], (
                    f"Undirected edge {node}-{neighbor} not symmetric"
                )

    def test_empty_graph(self):
        g = gen_graph(edge_density=0.0)
        result = g(5)
        for neighbors in result.values():
            assert neighbors == []


class TestGenMatrix:
    def test_basic(self):
        g = gen_matrix()
        result = g(5)
        assert len(result) == 5
        assert all(len(row) == 5 for row in result)

    def test_value_range(self):
        g = gen_matrix(value_range=(0, 1))
        result = g(10)
        for row in result:
            for val in row:
                assert 0 <= val <= 1


class TestGenNestedDict:
    def test_basic(self):
        g = gen_nested_dict(depth=2)
        result = g(3)
        assert len(result) == 3
        for v in result.values():
            assert isinstance(v, dict)
            assert len(v) == 3

    def test_depth_one(self):
        g = gen_nested_dict(depth=1)
        result = g(5)
        for v in result.values():
            assert isinstance(v, dict)
            for inner_v in v.values():
                assert isinstance(inner_v, int)
