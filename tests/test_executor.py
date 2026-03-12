"""Tests for bardic.runtime.executor — CommandExecutor in isolation."""

import pytest

from bardic.runtime.executor import CommandExecutor
from bardic.runtime.hooks import HookManager


def _make_executor(state=None, context=None):
    """Create a CommandExecutor with fresh state."""
    state = state if state is not None else {}
    context = context if context is not None else {}
    return CommandExecutor(
        state=state,
        context=context,
        local_scope_stack=[],
        hook_manager=HookManager(),
    )


class TestGetSafeBuiltins:
    """Tests for the restricted builtins dict."""

    def test_includes_type_constructors(self):
        ex = _make_executor()
        builtins = ex.get_safe_builtins()
        assert builtins["int"] is int
        assert builtins["str"] is str
        assert builtins["list"] is list
        assert builtins["dict"] is dict

    def test_includes_math(self):
        ex = _make_executor()
        builtins = ex.get_safe_builtins()
        assert builtins["sum"] is sum
        assert builtins["min"] is min
        assert builtins["max"] is max
        assert builtins["abs"] is abs

    def test_includes_import(self):
        ex = _make_executor()
        builtins = ex.get_safe_builtins()
        assert "__import__" in builtins

    def test_no_dangerous_builtins(self):
        ex = _make_executor()
        builtins = ex.get_safe_builtins()
        assert "exec" not in builtins
        assert "eval" not in builtins
        assert "compile" not in builtins
        assert "open" not in builtins


class TestGetEvalContext:
    """Tests for evaluation context building."""

    def test_includes_state(self):
        ex = _make_executor(state={"hp": 100})
        ctx = ex.get_eval_context()
        assert ctx["hp"] == 100

    def test_includes_context(self):
        ex = _make_executor(context={"MyClass": dict})
        ctx = ex.get_eval_context()
        assert ctx["MyClass"] is dict

    def test_includes_state_reference(self):
        state = {"x": 1}
        ex = _make_executor(state=state)
        ctx = ex.get_eval_context()
        assert ctx["_state"] is state

    def test_includes_local_scope(self):
        ex = _make_executor(state={"x": 1})
        ex._local_scope_stack.append({"param": 42})
        ctx = ex.get_eval_context()
        assert ctx["param"] == 42
        assert ctx["_local"]["param"] == 42

    def test_empty_local_when_no_scope(self):
        ex = _make_executor()
        ctx = ex.get_eval_context()
        assert ctx["_local"] == {}


class TestExecuteCommands:
    """Tests for command execution."""

    def test_python_statement(self):
        state = {}
        ex = _make_executor(state=state)
        ex.execute_commands([{"type": "python_statement", "code": "x = 42"}])
        assert state["x"] == 42

    def test_set_var(self):
        state = {}
        ex = _make_executor(state=state)
        ex.execute_commands([{"type": "set_var", "var": "name", "expression": '"Hero"'}])
        assert state["name"] == "Hero"

    def test_expression_statement(self):
        results = []
        state = {"results": results}
        ex = _make_executor(state=state)
        ex.execute_commands([
            {"type": "expression_statement", "code": "results.append(1)"}
        ])
        assert results == [1]

    def test_python_block(self):
        state = {}
        ex = _make_executor(state=state)
        ex.execute_commands([{"type": "python_block", "code": "x = 10\ny = x * 2"}])
        assert state["x"] == 10
        assert state["y"] == 20

    def test_hook_command(self):
        state = {}
        hm = HookManager()
        ex = CommandExecutor(state=state, context={}, local_scope_stack=[], hook_manager=hm)
        ex.execute_commands([
            {"type": "hook", "action": "add", "event": "turn_end", "target": "Ticker"}
        ])
        assert hm.get_handlers("turn_end") == ["Ticker"]

    def test_set_var_with_expression(self):
        state = {"base": 10}
        ex = _make_executor(state=state)
        ex.execute_commands([
            {"type": "set_var", "var": "result", "expression": "base * 3"}
        ])
        assert state["result"] == 30


class TestParseLiteral:
    """Tests for literal value parsing."""

    def test_true(self):
        assert CommandExecutor.parse_literal("true") is True
        assert CommandExecutor.parse_literal("True") is True

    def test_false(self):
        assert CommandExecutor.parse_literal("false") is False

    def test_integer(self):
        assert CommandExecutor.parse_literal("42") == 42

    def test_float(self):
        assert CommandExecutor.parse_literal("3.14") == 3.14

    def test_quoted_string(self):
        assert CommandExecutor.parse_literal('"hello"') == "hello"
        assert CommandExecutor.parse_literal("'world'") == "world"

    def test_unquoted_string(self):
        assert CommandExecutor.parse_literal("Hero") == "Hero"


class TestErrorHandling:
    """Tests for error reporting."""

    def test_bad_python_statement_raises(self):
        ex = _make_executor()
        with pytest.raises(RuntimeError, match="Python statement failed"):
            ex.execute_python_statement({"code": "undefined_var + 1"})

    def test_bad_set_var_raises(self):
        """set_var with a truly unresolvable expression raises RuntimeError.

        Note: simple strings like 'bogus' fall through to parse_literal and
        get stored as string values. We need something that fails both eval
        AND parse_literal — an assignment to a dotted path with bad expression.
        """
        ex = _make_executor()
        with pytest.raises(RuntimeError, match="Variable assignment failed"):
            ex.execute_set_var({"var": "obj.attr", "expression": "undefined_var + 1"})

    def test_bad_expression_statement_raises(self):
        ex = _make_executor()
        with pytest.raises(RuntimeError, match="Expression statement failed"):
            ex.execute_expression_statement({"code": "nonexistent()"})

    def test_bad_python_block_raises(self):
        ex = _make_executor()
        with pytest.raises(RuntimeError):
            ex.execute_python_block({"code": "def bad syntax"})


class TestImportPaths:
    """Tests for CommandExecutor import accessibility."""

    def test_import_from_executor_module(self):
        from bardic.runtime.executor import CommandExecutor as CE
        assert CE is CommandExecutor

    def test_import_from_runtime_package(self):
        from bardic.runtime import CommandExecutor as CE
        assert CE is CommandExecutor
