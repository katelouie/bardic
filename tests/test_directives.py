"""Tests for bardic.runtime.directives — DirectiveProcessor in isolation."""

import pytest

from bardic.runtime.directives import DirectiveProcessor


def _make_processor(state=None, context=None, evaluate_directives=True):
    """Create a DirectiveProcessor with mock providers."""
    state = state or {}
    context = context or {}
    builtins = {
        "abs": abs,
        "len": len,
        "max": max,
        "min": min,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "dict": dict,
        "range": range,
    }
    eval_ctx = {"__builtins__": builtins, **state, **context}

    return DirectiveProcessor(
        eval_context_provider=lambda: dict(eval_ctx),
        builtins_provider=lambda: builtins,
        state_provider=lambda: state,
        framework_processors={"react": DirectiveProcessor.process_for_react},
    )


class TestParseDirectiveArgs:
    """Tests for argument parsing via AST."""

    def test_positional_args(self):
        proc = _make_processor()
        builtins = proc._get_builtins()
        result = proc.parse_directive_args("1, 2, 3", {}, builtins)
        assert result == {"arg_0": 1, "arg_1": 2, "arg_2": 3}

    def test_keyword_args(self):
        proc = _make_processor()
        builtins = proc._get_builtins()
        result = proc.parse_directive_args("x=10, y=20", {}, builtins)
        assert result == {"x": 10, "y": 20}

    def test_mixed_args(self):
        proc = _make_processor()
        builtins = proc._get_builtins()
        result = proc.parse_directive_args('"hello", count=3', {}, builtins)
        assert result == {"arg_0": "hello", "count": 3}

    def test_empty_args(self):
        proc = _make_processor()
        builtins = proc._get_builtins()
        result = proc.parse_directive_args("", {}, builtins)
        assert result == {}

    def test_expression_args(self):
        proc = _make_processor(state={"gold": 100})
        ctx = proc._get_eval_context()
        builtins = proc._get_builtins()
        result = proc.parse_directive_args("gold * 2", ctx, builtins)
        assert result == {"arg_0": 200}

    def test_invalid_args_raises(self):
        proc = _make_processor()
        builtins = proc._get_builtins()
        with pytest.raises(ValueError, match="Could not parse"):
            proc.parse_directive_args("invalid syntax !!!", {}, builtins)


class TestBindArguments:
    """Tests for parameter binding."""

    def test_positional_binding(self):
        proc = _make_processor()
        params = [{"name": "x", "default": None}, {"name": "y", "default": None}]
        arg_dict = {"arg_0": 10, "arg_1": 20}
        result = proc.bind_arguments(params, arg_dict)
        assert result == {"x": 10, "y": 20}

    def test_keyword_binding(self):
        proc = _make_processor()
        params = [{"name": "x", "default": None}, {"name": "y", "default": None}]
        arg_dict = {"x": 10, "y": 20}
        result = proc.bind_arguments(params, arg_dict)
        assert result == {"x": 10, "y": 20}

    def test_default_values(self):
        proc = _make_processor()
        params = [{"name": "x", "default": None}, {"name": "y", "default": "42"}]
        arg_dict = {"arg_0": 10}
        result = proc.bind_arguments(params, arg_dict)
        assert result == {"x": 10, "y": 42}

    def test_missing_required_raises(self):
        proc = _make_processor()
        params = [{"name": "x", "default": None}]
        with pytest.raises(ValueError, match="Required parameter"):
            proc.bind_arguments(params, {})


class TestProcessRenderDirective:
    """Tests for full directive processing."""

    def test_evaluated_mode(self):
        proc = _make_processor(state={"name": "Alice"})
        directive = {"name": "greeting", "args": "name", "framework_hint": None}
        result = proc.process_render_directive(directive, evaluate=True)
        assert result["type"] == "render_directive"
        assert result["name"] == "greeting"
        assert result["mode"] == "evaluated"
        assert result["data"]["arg_0"] == "Alice"

    def test_raw_mode(self):
        proc = _make_processor(state={"hp": 100})
        directive = {"name": "health_bar", "args": "hp", "framework_hint": None}
        result = proc.process_render_directive(directive, evaluate=False)
        assert result["mode"] == "raw"
        assert result["raw_args"] == "hp"
        assert result["state_snapshot"]["hp"] == 100

    def test_react_framework_hint(self):
        proc = _make_processor()
        directive = {
            "name": "card_detail",
            "args": '"The Fool"',
            "framework_hint": "react",
        }
        result = proc.process_render_directive(directive, evaluate=True)
        assert result["framework"] == "react"
        assert result["react"]["componentName"] == "CardDetail"
        assert result["react"]["props"]["arg_0"] == "The Fool"

    def test_error_mode_on_bad_expression(self):
        proc = _make_processor()
        directive = {"name": "broken", "args": "undefined_var", "framework_hint": None}
        result = proc.process_render_directive(directive, evaluate=True)
        assert result["mode"] == "error"
        assert "error" in result

    def test_no_args(self):
        proc = _make_processor()
        directive = {"name": "separator", "args": "", "framework_hint": None}
        result = proc.process_render_directive(directive, evaluate=True)
        assert result["data"] == {}


class TestProcessForReact:
    """Tests for React-specific output."""

    def test_pascal_case_conversion(self):
        result = DirectiveProcessor.process_for_react("card_detail", {"title": "Foo"})
        assert result["componentName"] == "CardDetail"

    def test_single_word(self):
        result = DirectiveProcessor.process_for_react("header", {})
        assert result["componentName"] == "Header"

    def test_unique_key(self):
        r1 = DirectiveProcessor.process_for_react("card", {})
        r2 = DirectiveProcessor.process_for_react("card", {})
        assert r1["key"] != r2["key"]
        assert r1["key"].startswith("card_")

    def test_props_passed_through(self):
        result = DirectiveProcessor.process_for_react("widget", {"x": 1, "y": 2})
        assert result["props"] == {"x": 1, "y": 2}


class TestImportPaths:
    """Tests for DirectiveProcessor import accessibility."""

    def test_import_from_directives_module(self):
        from bardic.runtime.directives import DirectiveProcessor as DP

        assert DP is DirectiveProcessor

    def test_import_from_runtime_package(self):
        from bardic.runtime import DirectiveProcessor as DP

        assert DP is DirectiveProcessor
