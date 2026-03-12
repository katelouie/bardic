"""Tests for bardic.runtime.renderer — ContentRenderer in isolation."""

import pytest

from bardic.runtime.renderer import ContentRenderer
from bardic.runtime.executor import CommandExecutor
from bardic.runtime.directives import DirectiveProcessor
from bardic.runtime.hooks import HookManager


def _make_renderer(state=None, passages=None, used_choices=None, evaluate_directives=True):
    """Create a ContentRenderer with fresh state and minimal dependencies."""
    state = state if state is not None else {}
    passages = passages if passages is not None else {}
    used_choices = used_choices if used_choices is not None else set()
    local_scope_stack = []
    hook_manager = HookManager()
    join_section_index = {}

    executor = CommandExecutor(
        state=state,
        context={},
        local_scope_stack=local_scope_stack,
        hook_manager=hook_manager,
    )

    directive_processor = DirectiveProcessor(
        eval_context_provider=executor.get_eval_context,
        builtins_provider=executor.get_safe_builtins,
        state_provider=lambda: state,
    )

    renderer = ContentRenderer(
        eval_context_provider=executor.get_eval_context,
        builtins_provider=executor.get_safe_builtins,
        state=state,
        local_scope_stack=local_scope_stack,
        executor=executor,
        directive_processor=directive_processor,
        passages=passages,
        used_choices=used_choices,
        join_section_index=join_section_index,
        evaluate_directives=evaluate_directives,
    )

    return renderer, state


class TestRenderContent:
    """Tests for content token rendering."""

    def test_text_token(self):
        renderer, _ = _make_renderer()
        content, jump, directives = renderer.render_content(
            [{"type": "text", "value": "Hello world"}]
        )
        assert content == "Hello world"
        assert jump is None
        assert directives == []

    def test_expression_token(self):
        renderer, _ = _make_renderer(state={"name": "Alice"})
        content, _, _ = renderer.render_content(
            [{"type": "expression", "code": "name"}]
        )
        assert content == "Alice"

    def test_expression_with_format_spec(self):
        renderer, _ = _make_renderer(state={"price": 9.99})
        content, _, _ = renderer.render_content(
            [{"type": "expression", "code": "price:.2f"}]
        )
        assert content == "9.99"

    def test_expression_error_shows_debug(self):
        renderer, _ = _make_renderer()
        content, _, _ = renderer.render_content(
            [{"type": "expression", "code": "undefined_var"}]
        )
        assert "ERROR" in content
        assert "undefined_var" in content

    def test_mixed_text_and_expressions(self):
        renderer, _ = _make_renderer(state={"name": "Bob", "gold": 50})
        content, _, _ = renderer.render_content([
            {"type": "text", "value": "Hello "},
            {"type": "expression", "code": "name"},
            {"type": "text", "value": "! You have "},
            {"type": "expression", "code": "gold"},
            {"type": "text", "value": " gold."},
        ])
        assert content == "Hello Bob! You have 50 gold."

    def test_inline_conditional_truthy(self):
        renderer, _ = _make_renderer(state={"health": 80})
        content, _, _ = renderer.render_content([
            {"type": "inline_conditional", "condition": "health > 50",
             "truthy": [{"type": "text", "value": "Healthy"}],
             "falsy": [{"type": "text", "value": "Weak"}]},
        ])
        assert content == "Healthy"

    def test_inline_conditional_falsy(self):
        renderer, _ = _make_renderer(state={"health": 20})
        content, _, _ = renderer.render_content([
            {"type": "inline_conditional", "condition": "health > 50",
             "truthy": [{"type": "text", "value": "Healthy"}],
             "falsy": [{"type": "text", "value": "Weak"}]},
        ])
        assert content == "Weak"

    def test_jump_token_stops_rendering(self):
        renderer, _ = _make_renderer()
        content, jump, _ = renderer.render_content([
            {"type": "text", "value": "Before jump"},
            {"type": "jump", "target": "NextPassage"},
            {"type": "text", "value": "After jump"},
        ])
        assert content == "Before jump"
        assert jump == "NextPassage"

    def test_python_statement_executes(self):
        renderer, state = _make_renderer()
        renderer.render_content([
            {"type": "python_statement", "code": "x = 42"},
        ])
        assert state["x"] == 42

    def test_python_block_executes(self):
        renderer, state = _make_renderer()
        renderer.render_content([
            {"type": "python_block", "code": "a = 10\nb = a * 2"},
        ])
        assert state["a"] == 10
        assert state["b"] == 20

    def test_set_var_executes(self):
        renderer, state = _make_renderer()
        renderer.render_content([
            {"type": "set_var", "var": "name", "expression": '"Hero"'},
        ])
        assert state["name"] == "Hero"

    def test_join_marker_stops_rendering(self):
        renderer, _ = _make_renderer()
        content, _, _ = renderer.render_content([
            {"type": "text", "value": "Before join"},
            {"type": "join_marker"},
            {"type": "text", "value": "After join"},
        ])
        assert content == "Before join"

    def test_input_directive_collected(self):
        renderer, _ = _make_renderer()
        _, _, directives = renderer.render_content([
            {"type": "input", "name": "player_name", "prompt": "Enter name"},
        ])
        assert len(directives) == 1
        assert directives[0]["type"] == "input"

    def test_hook_executes_during_render(self):
        renderer, _ = _make_renderer()
        renderer.render_content([
            {"type": "hook", "action": "add", "event": "turn_end", "target": "Ticker"},
        ])
        assert renderer._executor.hook_manager.get_handlers("turn_end") == ["Ticker"]


class TestRenderLoop:
    """Tests for loop rendering."""

    def test_basic_loop(self):
        renderer, state = _make_renderer(state={"items": ["sword", "shield", "potion"]})
        content, _, _ = renderer.render_loop({
            "variable": "item",
            "collection": "items",
            "content": [
                {"type": "text", "value": "- "},
                {"type": "expression", "code": "item"},
                {"type": "text", "value": "\n"},
            ],
        })
        assert "sword" in content
        assert "shield" in content
        assert "potion" in content

    def test_loop_restores_state(self):
        renderer, state = _make_renderer(state={"items": [1, 2, 3], "item": "original"})
        renderer.render_loop({
            "variable": "item",
            "collection": "items",
            "content": [{"type": "expression", "code": "item"}],
        })
        assert state["item"] == "original"

    def test_empty_loop(self):
        renderer, _ = _make_renderer()
        content, jump, directives = renderer.render_loop({
            "variable": "",
            "collection": "",
            "content": [],
        })
        assert content == ""
        assert jump is None
        assert directives == []

    def test_loop_with_jump(self):
        renderer, state = _make_renderer(state={"items": ["a", "b", "c"]})
        content, jump, _ = renderer.render_loop({
            "variable": "item",
            "collection": "items",
            "content": [
                {"type": "jump", "target": "Exit"},
            ],
        })
        assert jump == "Exit"

    def test_tuple_unpacking(self):
        renderer, state = _make_renderer(state={"pairs": [("a", 1), ("b", 2)]})
        content, _, _ = renderer.render_loop({
            "variable": "key, val",
            "collection": "pairs",
            "content": [
                {"type": "expression", "code": "key"},
                {"type": "text", "value": "="},
                {"type": "expression", "code": "val"},
                {"type": "text", "value": " "},
            ],
        })
        assert "a=1" in content
        assert "b=2" in content


class TestRenderConditional:
    """Tests for conditional block rendering."""

    def test_true_branch(self):
        renderer, _ = _make_renderer(state={"x": 10})
        content, _, _ = renderer.render_conditional({
            "branches": [
                {"condition": "x > 5", "content": [{"type": "text", "value": "Big"}]},
                {"condition": "True", "content": [{"type": "text", "value": "Small"}]},
            ]
        })
        assert content == "Big"

    def test_false_falls_through(self):
        renderer, _ = _make_renderer(state={"x": 2})
        content, _, _ = renderer.render_conditional({
            "branches": [
                {"condition": "x > 5", "content": [{"type": "text", "value": "Big"}]},
                {"condition": "True", "content": [{"type": "text", "value": "Small"}]},
            ]
        })
        assert content == "Small"

    def test_no_branch_true(self):
        renderer, _ = _make_renderer(state={"x": 2})
        content, _, _ = renderer.render_conditional({
            "branches": [
                {"condition": "x > 100", "content": [{"type": "text", "value": "Huge"}]},
            ]
        })
        assert content == ""

    def test_conditional_with_jump(self):
        renderer, _ = _make_renderer(state={"dead": True})
        content, jump, _ = renderer.render_conditional({
            "branches": [
                {"condition": "dead", "content": [
                    {"type": "text", "value": "You died. "},
                    {"type": "jump", "target": "GameOver"},
                ]},
            ]
        })
        assert jump == "GameOver"

    def test_conditional_with_choices(self):
        renderer, _ = _make_renderer(state={"has_sword": True})
        content, _, directives = renderer.render_conditional({
            "branches": [
                {"condition": "has_sword", "content": [
                    {"type": "text", "value": "You draw your sword."},
                ], "choices": [
                    {"text": "Attack", "target": "Fight"},
                ]},
            ]
        })
        assert content == "You draw your sword."
        assert any(d.get("text") == "Attack" for d in directives)


class TestRenderChoiceText:
    """Tests for choice text rendering."""

    def test_string_text_passthrough(self):
        renderer, _ = _make_renderer()
        result = renderer.render_choice_text({"text": "Go north", "target": "North"})
        assert result["text"] == "Go north"
        assert result["target"] == "North"

    def test_tokenized_text(self):
        renderer, _ = _make_renderer(state={"gold": 50})
        result = renderer.render_choice_text({
            "text": [
                {"type": "text", "value": "Buy ("},
                {"type": "expression", "code": "gold"},
                {"type": "text", "value": " gold)"},
            ],
            "target": "Shop",
        })
        assert result["text"] == "Buy (50 gold)"


class TestIsChoiceAvailable:
    """Tests for choice availability checking."""

    def test_unconditional_choice_available(self):
        renderer, _ = _make_renderer()
        assert renderer.is_choice_available(
            {"text": "Go", "target": "Next"}, "Start"
        ) is True

    def test_true_condition(self):
        renderer, _ = _make_renderer(state={"has_key": True})
        assert renderer.is_choice_available(
            {"text": "Unlock", "target": "Door", "condition": "has_key"}, "Start"
        ) is True

    def test_false_condition(self):
        renderer, _ = _make_renderer(state={"has_key": False})
        assert renderer.is_choice_available(
            {"text": "Unlock", "target": "Door", "condition": "has_key"}, "Start"
        ) is False

    def test_one_time_choice_hidden_after_use(self):
        renderer, _ = _make_renderer(
            used_choices={"Room:Look around:Room"}
        )
        assert renderer.is_choice_available(
            {"text": "Look around", "target": "Room", "sticky": False}, "Room"
        ) is False

    def test_sticky_choice_always_available(self):
        renderer, _ = _make_renderer(
            used_choices={"Room:Look around:Room"}
        )
        assert renderer.is_choice_available(
            {"text": "Look around", "target": "Room", "sticky": True}, "Room"
        ) is True

    def test_bad_condition_hides_choice(self):
        renderer, _ = _make_renderer()
        # Undefined variable in condition — choice should be hidden
        assert renderer.is_choice_available(
            {"text": "Go", "target": "Next", "condition": "undefined_var"}, "Start"
        ) is False


class TestRenderPassage:
    """Tests for full passage rendering."""

    def test_basic_passage(self):
        passages = {
            "Start": {
                "content": [{"type": "text", "value": "Welcome!"}],
                "choices": [{"text": "Continue", "target": "Next"}],
            }
        }
        renderer, _ = _make_renderer(passages=passages)
        output = renderer.render_passage("Start", "Start")
        assert output.content == "Welcome!"
        assert len(output.choices) == 1
        assert output.choices[0]["text"] == "Continue"

    def test_passage_not_found(self):
        renderer, _ = _make_renderer()
        with pytest.raises(ValueError, match="not found"):
            renderer.render_passage("Missing", "Start")

    def test_passage_with_conditional_choice(self):
        passages = {
            "Room": {
                "content": [{"type": "text", "value": "A room."}],
                "choices": [
                    {"text": "Open door", "target": "Door", "condition": "has_key"},
                    {"text": "Look around", "target": "Room"},
                ],
            }
        }
        renderer, _ = _make_renderer(state={"has_key": False}, passages=passages)
        output = renderer.render_passage("Room", "Room")
        texts = [c["text"] for c in output.choices]
        assert "Look around" in texts
        assert "Open door" not in texts

    def test_passage_with_jump(self):
        passages = {
            "Redirect": {
                "content": [
                    {"type": "text", "value": "Redirecting..."},
                    {"type": "jump", "target": "Destination"},
                ],
                "choices": [],
            }
        }
        renderer, _ = _make_renderer(passages=passages)
        output = renderer.render_passage("Redirect", "Redirect")
        assert output.jump_target == "Destination"


class TestSplitFormatSpec:
    """Tests for format spec parsing."""

    def test_basic_format(self):
        expr, spec = ContentRenderer.split_format_spec("price:.2f")
        assert expr == "price"
        assert spec == ".2f"

    def test_no_format(self):
        expr, spec = ContentRenderer.split_format_spec("variable_name")
        assert expr == "variable_name"
        assert spec is None

    def test_comparison_not_split(self):
        expr, spec = ContentRenderer.split_format_spec("x == y")
        assert expr == "x == y"
        assert spec is None

    def test_slice_not_split(self):
        expr, spec = ContentRenderer.split_format_spec("items[0::2]")
        assert expr == "items[0::2]"
        assert spec is None


class TestImportPaths:
    """Tests for ContentRenderer import accessibility."""

    def test_import_from_renderer_module(self):
        from bardic.runtime.renderer import ContentRenderer as CR
        assert CR is ContentRenderer

    def test_import_from_runtime_package(self):
        from bardic.runtime import ContentRenderer as CR
        assert CR is ContentRenderer
