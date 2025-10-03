# test_engine_refactor.py

from bardic import BardEngine
import json


def test_no_double_execution():
    """Test that variables don't change on repeated current() calls"""

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

    engine = BardEngine(story)

    # X should be 1 after initialization
    assert engine.state["x"] == 1

    # Call current() multiple times
    output1 = engine.current()
    output2 = engine.current()
    output3 = engine.current()

    # X should still be 1 (not incremented each time)
    assert engine.state["x"] == 1
    assert output1.content == "X is 1"
    assert output2.content == "X is 1"
    assert output3.content == "X is 1"

    print("✓ No double execution!")


def test_goto_executes_once():
    """Test that goto executes commands exactly once"""

    story = {
        "version": "0.1.0",
        "initial_passage": "Start",
        "passages": {
            "Start": {
                "id": "Start",
                "execute": [{"type": "set_var", "var": "counter", "expression": "0"}],
                "content": [],
                "choices": [{"text": "Next", "target": "Increment", "condition": None}],
            },
            "Increment": {
                "id": "Increment",
                "execute": [
                    {"type": "set_var", "var": "counter", "expression": "counter + 1"}
                ],
                "content": [
                    {"type": "text", "value": "Counter: "},
                    {"type": "expression", "code": "counter"},
                ],
                "choices": [],
            },
        },
    }

    engine = BardEngine(story)

    # Counter starts at 0
    assert engine.state["counter"] == 0

    # Navigate to Increment
    output = engine.goto("Increment")

    # Counter should be 1 (incremented once)
    assert engine.state["counter"] == 1
    assert output.content == "Counter: 1"

    # Call current() multiple times - counter stays 1
    output = engine.current()
    assert engine.state["counter"] == 1
    output = engine.current()
    assert engine.state["counter"] == 1

    print("✓ goto executes exactly once!")


if __name__ == "__main__":
    test_no_double_execution()
    test_goto_executes_once()
    print("\n✅ All tests passed!")
