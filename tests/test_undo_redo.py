"""Test the Bardic undo/redo system."""

import pytest
from bardic.runtime.engine import BardEngine


@pytest.fixture
def undo_story():
    """A story for testing undo/redo functionality."""
    return {
        "version": "0.1.0",
        "initial_passage": "Start",
        "passages": {
            "Start": {
                "id": "Start",
                "content": [{"type": "text", "value": "You are at the start."}],
                "choices": [
                    {"text": "Go to A", "target": "PassageA"},
                    {"text": "Go to B", "target": "PassageB"},
                ],
                "execute": [{"type": "python_statement", "code": "visited = ['Start']"}],
            },
            "PassageA": {
                "id": "PassageA",
                "content": [{"type": "text", "value": "You are at passage A."}],
                "choices": [
                    {"text": "Go to C", "target": "PassageC"},
                    {"text": "Go to D", "target": "PassageD"},
                ],
                "execute": [{"type": "python_statement", "code": "visited.append('A')"}],
            },
            "PassageB": {
                "id": "PassageB",
                "content": [{"type": "text", "value": "You are at passage B."}],
                "choices": [{"text": "Go to C", "target": "PassageC"}],
                "execute": [{"type": "python_statement", "code": "visited.append('B')"}],
            },
            "PassageC": {
                "id": "PassageC",
                "content": [{"type": "text", "value": "You are at passage C."}],
                "choices": [],
                "execute": [{"type": "python_statement", "code": "visited.append('C')"}],
            },
            "PassageD": {
                "id": "PassageD",
                "content": [{"type": "text", "value": "You are at passage D."}],
                "choices": [],
                "execute": [{"type": "python_statement", "code": "visited.append('D')"}],
            },
        },
    }


class TestUndoBasics:
    """Test basic undo functionality."""

    def test_can_undo_is_false_at_start(self, undo_story):
        """can_undo() should return False when no choices have been made."""
        engine = BardEngine(undo_story)
        assert engine.can_undo() is False

    def test_can_undo_is_true_after_choice(self, undo_story):
        """can_undo() should return True after making a choice."""
        engine = BardEngine(undo_story)
        engine.choose(0)  # Go to A
        assert engine.can_undo() is True

    def test_undo_returns_to_previous_passage(self, undo_story):
        """undo() should return to the previous passage."""
        engine = BardEngine(undo_story)

        # Make a choice
        engine.choose(0)  # Go to A
        assert engine.current().passage_id == "PassageA"

        # Undo
        result = engine.undo()
        assert result is True
        assert engine.current().passage_id == "Start"

    def test_undo_restores_state(self, undo_story):
        """undo() should restore the previous state."""
        engine = BardEngine(undo_story)
        assert engine.state["visited"] == ["Start"]

        # Make a choice (modifies state)
        engine.choose(0)  # Go to A
        assert engine.state["visited"] == ["Start", "A"]

        # Undo
        engine.undo()
        assert engine.state["visited"] == ["Start"]

    def test_undo_returns_false_when_empty(self, undo_story):
        """undo() should return False when there's nothing to undo."""
        engine = BardEngine(undo_story)
        result = engine.undo()
        assert result is False

    def test_multiple_undos(self, undo_story):
        """Multiple undos should walk back through history."""
        engine = BardEngine(undo_story)

        # Make multiple choices
        engine.choose(0)  # Start -> A
        engine.choose(0)  # A -> C
        assert engine.current().passage_id == "PassageC"
        assert engine.state["visited"] == ["Start", "A", "C"]

        # Undo twice
        engine.undo()
        assert engine.current().passage_id == "PassageA"
        assert engine.state["visited"] == ["Start", "A"]

        engine.undo()
        assert engine.current().passage_id == "Start"
        assert engine.state["visited"] == ["Start"]


class TestRedoBasics:
    """Test basic redo functionality."""

    def test_can_redo_is_false_at_start(self, undo_story):
        """can_redo() should return False when nothing has been undone."""
        engine = BardEngine(undo_story)
        assert engine.can_redo() is False

    def test_can_redo_is_true_after_undo(self, undo_story):
        """can_redo() should return True after undoing."""
        engine = BardEngine(undo_story)
        engine.choose(0)
        engine.undo()
        assert engine.can_redo() is True

    def test_redo_returns_to_undone_state(self, undo_story):
        """redo() should return to the state before undo."""
        engine = BardEngine(undo_story)

        # Make a choice, then undo
        engine.choose(0)  # Go to A
        engine.undo()
        assert engine.current().passage_id == "Start"

        # Redo
        result = engine.redo()
        assert result is True
        assert engine.current().passage_id == "PassageA"
        assert engine.state["visited"] == ["Start", "A"]

    def test_redo_returns_false_when_empty(self, undo_story):
        """redo() should return False when there's nothing to redo."""
        engine = BardEngine(undo_story)
        result = engine.redo()
        assert result is False

    def test_new_choice_clears_redo_stack(self, undo_story):
        """Making a new choice after undo should clear the redo stack."""
        engine = BardEngine(undo_story)

        # Make choice, undo, make different choice
        engine.choose(0)  # Go to A
        engine.undo()
        engine.choose(1)  # Go to B (different choice)

        # Redo should now be empty
        assert engine.can_redo() is False


class TestUndoRedoWithHooks:
    """Test that undo/redo properly handles hook state."""

    @pytest.fixture
    def hook_undo_story(self):
        """Story with hooks for testing undo/redo interaction."""
        return {
            "version": "0.1.0",
            "initial_passage": "Start",
            "passages": {
                "Start": {
                    "id": "Start",
                    "content": [{"type": "text", "value": "Start."}],
                    "choices": [{"text": "Register hook", "target": "Register"}],
                    "execute": [{"type": "python_statement", "code": "counter = 0"}],
                },
                "Register": {
                    "id": "Register",
                    "content": [{"type": "text", "value": "Hook registered."}],
                    "choices": [{"text": "Continue", "target": "Room"}],
                    "execute": [{"type": "hook", "action": "add", "event": "turn_end", "target": "Counter"}],
                },
                "Counter": {
                    "id": "Counter",
                    "content": [],
                    "choices": [],
                    "execute": [{"type": "python_statement", "code": "counter = counter + 1"}],
                },
                "Room": {
                    "id": "Room",
                    "content": [{"type": "text", "value": "Room."}],
                    "choices": [{"text": "Stay", "target": "Room"}],
                    "execute": [],
                },
            },
        }

    def test_undo_restores_hook_state(self, hook_undo_story):
        """Undoing should restore hooks to their previous state."""
        engine = BardEngine(hook_undo_story)

        # Initially no hooks
        assert "turn_end" not in engine.hooks or len(engine.hooks.get("turn_end", [])) == 0

        # Register hook
        engine.choose(0)  # Go to Register
        assert "Counter" in engine.hooks.get("turn_end", [])

        # Undo - should remove the hook
        engine.undo()
        assert "Counter" not in engine.hooks.get("turn_end", [])


class TestUndoStackLimit:
    """Test that undo stack respects size limits."""

    def test_undo_stack_is_bounded(self, undo_story):
        """Undo stack should not grow beyond its limit."""
        engine = BardEngine(undo_story)

        # The default limit is 50, but we'll just verify the deque has maxlen
        assert hasattr(engine.undo_stack, 'maxlen')
        assert engine.undo_stack.maxlen == 50


class TestSnapshotIntegrity:
    """Test that snapshots capture complete state."""

    def test_snapshot_captures_used_choices(self, simple_story_with_sticky):
        """Snapshots should capture one-time choice usage."""
        engine = BardEngine(simple_story_with_sticky)

        # Use a one-time choice
        engine.choose(0)  # Use the one-time choice

        # The choice should be marked as used
        assert len(engine.used_choices) > 0
        used_before = engine.used_choices.copy()

        # Make another choice
        engine.choose(0)

        # Undo back
        engine.undo()
        engine.undo()

        # used_choices should be restored
        assert engine.used_choices == set()  # Back to start, nothing used


@pytest.fixture
def simple_story_with_sticky():
    """Story with one-time (non-sticky) choices for testing."""
    return {
        "version": "0.1.0",
        "initial_passage": "Start",
        "passages": {
            "Start": {
                "id": "Start",
                "content": [{"type": "text", "value": "Start."}],
                "choices": [
                    {"text": "One-time choice", "target": "Middle", "sticky": False},
                    {"text": "Regular choice", "target": "Middle", "sticky": True},
                ],
                "execute": [],
            },
            "Middle": {
                "id": "Middle",
                "content": [{"type": "text", "value": "Middle."}],
                "choices": [{"text": "Continue", "target": "End"}],
                "execute": [],
            },
            "End": {
                "id": "End",
                "content": [{"type": "text", "value": "End."}],
                "choices": [],
                "execute": [],
            },
        },
    }
