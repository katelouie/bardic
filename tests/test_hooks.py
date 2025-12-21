"""Test the Bardic hooks system."""

import pytest
from bardic.runtime.engine import BardEngine


@pytest.fixture
def hook_story():
    """A story with hook functionality for testing."""
    return {
        "version": "0.1.0",
        "initial_passage": "Start",
        "passages": {
            "Start": {
                "id": "Start",
                "content": [{"type": "text", "value": "Welcome!"}],
                "choices": [
                    {"text": "Register hook", "target": "RegisterHook"},
                    {"text": "Skip", "target": "Room"},
                ],
                "execute": [{"type": "python_statement", "code": "counter = 0"}],
            },
            "RegisterHook": {
                "id": "RegisterHook",
                "content": [{"type": "text", "value": "Hook registered."}],
                "choices": [{"text": "Continue", "target": "Room"}],
                "execute": [{"type": "hook", "action": "add", "event": "turn_end", "target": "CounterHook"}],
            },
            "CounterHook": {
                "id": "CounterHook",
                "content": [],
                "choices": [],
                "execute": [{"type": "python_statement", "code": "counter = counter + 1"}],
            },
            "Room": {
                "id": "Room",
                "content": [{"type": "text", "value": "You are in a room."}],
                "choices": [
                    {"text": "Stay", "target": "Room"},
                    {"text": "Unregister", "target": "Unregister"},
                ],
                "execute": [],
            },
            "Unregister": {
                "id": "Unregister",
                "content": [{"type": "text", "value": "Hook removed."}],
                "choices": [{"text": "Continue", "target": "Room"}],
                "execute": [{"type": "hook", "action": "remove", "event": "turn_end", "target": "CounterHook"}],
            },
        },
    }


class TestHookRegistration:
    """Test hook registration and unregistration."""

    def test_register_hook_adds_to_hooks_dict(self, hook_story):
        """register_hook() should add passage to hooks dictionary."""
        engine = BardEngine(hook_story)

        # When: We register a hook
        engine.register_hook("test_event", "SomePassage")

        # Then: It should be in the hooks dict
        assert "test_event" in engine.hooks
        assert "SomePassage" in engine.hooks["test_event"]

    def test_register_hook_is_idempotent(self, hook_story):
        """Registering the same hook twice should not create duplicates."""
        engine = BardEngine(hook_story)

        # When: We register the same hook twice
        engine.register_hook("test_event", "SomePassage")
        engine.register_hook("test_event", "SomePassage")

        # Then: It should only appear once
        assert engine.hooks["test_event"].count("SomePassage") == 1

    def test_unregister_hook_removes_from_hooks_dict(self, hook_story):
        """unregister_hook() should remove passage from hooks dictionary."""
        engine = BardEngine(hook_story)
        engine.register_hook("test_event", "SomePassage")

        # When: We unregister the hook
        engine.unregister_hook("test_event", "SomePassage")

        # Then: It should be removed
        assert "SomePassage" not in engine.hooks.get("test_event", [])

    def test_unregister_nonexistent_hook_does_not_crash(self, hook_story):
        """Unregistering a hook that doesn't exist should not raise."""
        engine = BardEngine(hook_story)

        # When/Then: Unregistering non-existent hook should not raise
        engine.unregister_hook("nonexistent_event", "NonexistentPassage")
        # No exception = pass


class TestHookExecution:
    """Test that hooks fire correctly."""

    def test_hook_fires_on_turn_end(self, hook_story):
        """Hooks registered to turn_end should fire after choose()."""
        engine = BardEngine(hook_story)
        assert engine.state.get("counter") == 0

        # When: We register hook and make a choice
        engine.choose(0)  # Register hook
        # Hook fires at end of this turn
        assert engine.state.get("counter") == 1

        # And: We make another choice
        engine.choose(0)  # Continue to Room
        # Hook fires again
        assert engine.state.get("counter") == 2

    def test_hook_stops_firing_after_unregister(self, hook_story):
        """Hooks should stop firing after being unregistered."""
        engine = BardEngine(hook_story)

        # Setup: Register hook and verify it fires
        engine.choose(0)  # Register hook -> counter = 1
        engine.choose(0)  # Continue to Room -> counter = 2
        counter_before = engine.state.get("counter")
        assert counter_before == 2

        # When: We unregister the hook
        # The @unhook runs during passage execution, BEFORE turn_end fires
        # So the hook is already gone when turn_end triggers
        engine.choose(1)  # Unregister -> counter stays 2 (hook already removed)

        counter_after_unregister = engine.state.get("counter")
        assert counter_after_unregister == 2  # Hook didn't fire (was unregistered first)

        # And: Further choices should not trigger the hook
        engine.choose(0)  # Continue to Room
        counter_final = engine.state.get("counter")
        assert counter_final == 2  # Still 2, hook is gone

    def test_multiple_hooks_fire_in_order(self, hook_story):
        """Multiple hooks on same event should fire in FIFO order."""
        engine = BardEngine(hook_story)
        engine.state["log"] = []

        # Create passages that log their execution
        engine.passages["HookA"] = {
            "id": "HookA",
            "content": [],
            "choices": [],
            "execute": [{"type": "python_statement", "code": "log.append('A')"}],
        }
        engine.passages["HookB"] = {
            "id": "HookB",
            "content": [],
            "choices": [],
            "execute": [{"type": "python_statement", "code": "log.append('B')"}],
        }

        # When: We register hooks in order A, B
        engine.register_hook("turn_end", "HookA")
        engine.register_hook("turn_end", "HookB")

        # And: Trigger the event
        engine.trigger_event("turn_end")

        # Then: They should have fired in order
        assert engine.state["log"] == ["A", "B"]


class TestHookDirectiveParsing:
    """Test that @hook/@unhook directives are parsed correctly."""

    def test_hook_directive_in_passage(self, compile_string):
        """@hook directive should create a hook command in execute."""
        story = compile_string("""
:: Start
@hook turn_end MyHook
Hello!
+ [Continue] -> End

:: MyHook
Hook content.

:: End
The end.
""")
        # Then: Start passage should have hook in execute
        start = story["passages"]["Start"]
        hook_cmds = [cmd for cmd in start["execute"] if cmd.get("type") == "hook"]
        assert len(hook_cmds) == 1
        assert hook_cmds[0]["action"] == "add"
        assert hook_cmds[0]["event"] == "turn_end"
        assert hook_cmds[0]["target"] == "MyHook"

    def test_unhook_directive_in_passage(self, compile_string):
        """@unhook directive should create a hook remove command in execute."""
        story = compile_string("""
:: Start
@unhook turn_end MyHook
Hello!
+ [Continue] -> End

:: End
The end.
""")
        # Then: Start passage should have unhook in execute
        start = story["passages"]["Start"]
        hook_cmds = [cmd for cmd in start["execute"] if cmd.get("type") == "hook"]
        assert len(hook_cmds) == 1
        assert hook_cmds[0]["action"] == "remove"
        assert hook_cmds[0]["event"] == "turn_end"
        assert hook_cmds[0]["target"] == "MyHook"

    def test_hook_directive_inside_conditional(self, compile_string):
        """@hook inside @if block should be parsed as hook token, not text."""
        story = compile_string("""
:: Start
~ should_hook = True
@if should_hook:
@hook turn_end MyHook
@endif
+ [Continue] -> End

:: MyHook
Hook passage.

:: End
Done.
""")
        # Then: The conditional branch should contain a hook token
        start = story["passages"]["Start"]
        conditional = None
        for token in start["content"]:
            if token.get("type") == "conditional":
                conditional = token
                break

        assert conditional is not None
        branch_content = conditional["branches"][0]["content"]
        hook_tokens = [t for t in branch_content if t.get("type") == "hook"]
        assert len(hook_tokens) == 1
        assert hook_tokens[0]["action"] == "add"

    def test_unhook_directive_inside_loop(self, compile_string):
        """@unhook inside @for block should be parsed as hook token."""
        story = compile_string("""
:: Start
~ hooks_to_remove = ["HookA", "HookB"]
@for hook in hooks_to_remove:
@unhook turn_end {hook}
@endfor
+ [Continue] -> End

:: End
Done.
""")
        # Then: The loop should contain unhook tokens
        start = story["passages"]["Start"]
        loop = None
        for token in start["content"]:
            if token.get("type") == "for_loop":
                loop = token
                break

        assert loop is not None
        # Note: The loop content has @unhook with {hook} which may need expression evaluation
        # For now just verify it's parsed as a hook type, not text
        hook_tokens = [t for t in loop["content"] if t.get("type") == "hook"]
        assert len(hook_tokens) == 1
        assert hook_tokens[0]["action"] == "remove"
