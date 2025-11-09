"""Test that the engine's execute/render separation works correctly."""

import pytest
from bardic.runtime.engine import BardEngine


class TestExecuteOnce:
    """
    Critical tests ensuring commands execute exactly once per navigation.

    This is a core guarantee of the engine architecture.
    """

    def test_current_does_not_re_execute(self):
        """Calling current() multiple times should not re-execute commands."""
        # Given: A story that increments x
        story = {
            "version": "0.1.0",
            "initial_passage": "Start",
            "passages": {
                "Start": {
                    "id": "Start",
                    "execute": [
                        {"type": "set_var", "var": "x", "expression": "0"},
                        {"type": "set_var", "var": "x", "expression": "x + 1"},
                    ],
                    "content": [
                        {"type": "text", "value": "X is "},
                        {"type": "expression", "code": "x"},
                    ],
                    "choices": [],
                }
            },
        }

        # When: We create the engine (which executes Start)
        engine = BardEngine(story)

        # Then: x should be 1
        assert engine.state["x"] == 1

        # When: We call current() multiple times
        output1 = engine.current()
        output2 = engine.current()
        output3 = engine.current()

        # Then: x should STILL be 1 (not incremented each time)
        assert engine.state["x"] == 1
        assert output1.content == "X is 1"
        assert output2.content == "X is 1"
        assert output3.content == "X is 1"

    def test_goto_executes_exactly_once(self):
        """goto() should execute passage commands exactly once."""
        # Given: A story with a counter
        story = {
            "version": "0.1.0",
            "initial_passage": "Start",
            "passages": {
                "Start": {
                    "id": "Start",
                    "execute": [
                        {"type": "set_var", "var": "counter", "expression": "0"}
                    ],
                    "content": [],
                    "choices": [{"text": "Next", "target": "Increment"}],
                },
                "Increment": {
                    "id": "Increment",
                    "execute": [
                        {
                            "type": "set_var",
                            "var": "counter",
                            "expression": "counter + 1",
                        }
                    ],
                    "content": [
                        {"type": "text", "value": "Counter: "},
                        {"type": "expression", "code": "counter"},
                    ],
                    "choices": [],
                },
            },
        }

        # When: We create engine and navigate
        engine = BardEngine(story)
        assert engine.state["counter"] == 0

        # When: We goto Increment
        output = engine.goto("Increment")

        # Then: Counter should be 1 (incremented once)
        assert engine.state["counter"] == 1
        assert output.content == "Counter: 1"

        # When: We call current() multiple times
        engine.current()
        engine.current()

        # Then: Counter should still be 1
        assert engine.state["counter"] == 1
