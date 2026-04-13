"""Tests for the CLI module."""

import pytest
import sys

from complexion.cli import _import_callable, build_parser


class TestImportCallable:
    def test_import_builtin_module(self):
        fn = _import_callable("json:dumps")
        import json
        assert fn is json.dumps

    def test_import_math_function(self):
        fn = _import_callable("math:sqrt")
        assert fn(4) == 2.0

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid callable spec"):
            _import_callable("no_colon_here")

    def test_nonexistent_module(self):
        with pytest.raises(ImportError):
            _import_callable("nonexistent_module_xyz:func")

    def test_nonexistent_attribute(self):
        with pytest.raises(AttributeError):
            _import_callable("json:nonexistent_attr_xyz")

    def test_not_callable(self):
        with pytest.raises(TypeError, match="not callable"):
            _import_callable("sys:path")


class TestBuildParser:
    def test_analyze_command(self):
        parser = build_parser()
        args = parser.parse_args([
            "analyze", "mymod:func", "-g", "mymod:gen"
        ])
        assert args.command == "analyze"
        assert args.function == "mymod:func"
        assert args.generator == "mymod:gen"

    def test_compare_command(self):
        parser = build_parser()
        args = parser.parse_args([
            "compare", "mod:f1", "mod:f2", "-g", "mod:gen"
        ])
        assert args.command == "compare"
        assert args.functions == ["mod:f1", "mod:f2"]

    def test_custom_sizes(self):
        parser = build_parser()
        args = parser.parse_args([
            "analyze", "mod:f", "-g", "mod:g",
            "--min-n", "50", "--max-n", "5000", "--points", "10",
        ])
        assert args.min_n == 50
        assert args.max_n == 5000
        assert args.points == 10

    def test_no_memory_flag(self):
        parser = build_parser()
        args = parser.parse_args([
            "analyze", "mod:f", "-g", "mod:g", "--no-memory",
        ])
        assert args.no_memory is True
