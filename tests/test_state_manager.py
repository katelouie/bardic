"""Tests for bardic.runtime.state — StateManager serialization and undo/redo."""

import json
import pytest

from bardic.runtime.state import StateManager
from bardic.runtime.engine import BardEngine
from bardic.compiler.compiler import BardCompiler


def _make_engine(story_str: str, **kwargs) -> BardEngine:
    """Helper to compile and create an engine from a .bard string."""
    compiler = BardCompiler()
    story_data = compiler.compile_string(story_str)
    return BardEngine(story_data, **kwargs)


# ── Serialization ──


class TestSerializeValue:
    """Tests for _serialize_value / _deserialize_value roundtrips."""

    def _sm(self) -> StateManager:
        """Get a StateManager with a minimal engine."""
        engine = _make_engine(":: Start\nHello")
        return engine.state_manager

    def test_primitives_roundtrip(self):
        """Strings, ints, floats, bools, None serialize as-is."""
        sm = self._sm()
        for val in ["hello", 42, 3.14, True, False, None]:
            assert sm._serialize_value(val) == val

    def test_list_roundtrip(self):
        """Lists serialize and deserialize correctly."""
        sm = self._sm()
        original = [1, "two", [3, 4]]
        serialized = sm._serialize_value(original)
        deserialized = sm._deserialize_value(serialized)
        assert deserialized == original

    def test_dict_roundtrip(self):
        """Plain dicts serialize and deserialize correctly."""
        sm = self._sm()
        original = {"a": 1, "b": {"nested": True}}
        serialized = sm._serialize_value(original)
        deserialized = sm._deserialize_value(serialized)
        assert deserialized == original

    def test_tuple_passes_json_check(self):
        """Tuples of primitives pass json.dumps (Priority 2) and stay as tuples.

        JSON serializes tuples as arrays, so they pass the json.dumps check
        before reaching the explicit tuple→list conversion in Priority 3.
        This is fine — json.dump will output them as arrays regardless.
        """
        sm = self._sm()
        serialized = sm._serialize_value((1, 2, 3))
        # json.dumps succeeds on tuples, so Priority 2 returns them as-is
        assert serialized == (1, 2, 3)
        # But they still serialize to JSON correctly
        assert json.dumps(serialized) == "[1, 2, 3]"

    def test_callable_becomes_none(self):
        """Callables (functions) serialize to None."""
        sm = self._sm()
        assert sm._serialize_value(lambda x: x) is None
        assert sm._serialize_value(print) is None

    def test_class_becomes_none(self):
        """Classes/types serialize to None."""
        sm = self._sm()
        assert sm._serialize_value(int) is None
        assert sm._serialize_value(str) is None

    def test_custom_to_save_dict(self):
        """Objects with to_save_dict() use custom serialization."""
        sm = self._sm()

        class Inventory:
            def __init__(self, items):
                self.items = items
            def to_save_dict(self):
                return {"items": self.items}

        inv = Inventory(["sword", "shield"])
        serialized = sm._serialize_value(inv)
        assert serialized["_type"] == "Inventory"
        assert serialized["_custom"] is True
        assert serialized["_data"]["items"] == ["sword", "shield"]

    def test_custom_from_save_dict_roundtrip(self):
        """Objects with both to_save_dict and from_save_dict roundtrip."""
        class Wallet:
            def __init__(self, gold):
                self.gold = gold
            def to_save_dict(self):
                return {"gold": self.gold}
            @classmethod
            def from_save_dict(cls, data):
                return cls(data["gold"])

        engine = _make_engine(":: Start\nHello", context={"Wallet": Wallet})
        sm = engine.state_manager

        original = Wallet(100)
        serialized = sm._serialize_value(original)
        deserialized = sm._deserialize_value(serialized)
        assert isinstance(deserialized, Wallet)
        assert deserialized.gold == 100

    def test_object_with_dict_fallback(self):
        """Objects without custom serialization use __dict__."""
        sm = self._sm()

        class Simple:
            def __init__(self):
                self.name = "test"
                self.value = 42

        obj = Simple()
        serialized = sm._serialize_value(obj)
        assert serialized["_type"] == "Simple"
        assert serialized["_data"]["name"] == "test"
        assert serialized["_data"]["value"] == 42


class TestSaveLoadState:
    """Tests for full save/load cycle through StateManager."""

    def test_save_produces_valid_json(self):
        """save_state() produces JSON-serializable output."""
        engine = _make_engine(":: Start\n~ x = 42\nHello\n+ [Go] -> End\n\n:: End\nDone")
        save_data = engine.save_state()
        # Should not raise
        json_str = json.dumps(save_data)
        assert isinstance(json_str, str)

    def test_save_captures_passage_id(self):
        """save_state() records the current passage."""
        engine = _make_engine(":: Start\nHello\n+ [Go] -> End\n\n:: End\nDone")
        save_data = engine.save_state()
        assert save_data["current_passage_id"] == "Start"

    def test_save_captures_state_variables(self):
        """save_state() includes game variables."""
        engine = _make_engine(":: Start\n~ gold = 100\nHello")
        save_data = engine.save_state()
        assert save_data["state"]["gold"] == 100

    def test_save_load_roundtrip(self):
        """Full save/load cycle restores state."""
        engine = _make_engine(
            ":: Start\n~ x = 10\nHello\n+ [Go] -> End\n\n:: End\n~ x = 99\nDone"
        )
        assert engine.state["x"] == 10

        # Save at Start
        save_data = engine.save_state()

        # Navigate to End
        engine.choose(0)
        assert engine.state["x"] == 99

        # Load — should restore to Start with x=10
        engine.load_state(save_data)
        assert engine.state["x"] == 10
        assert engine.current_passage_id == "Start"

    def test_load_validates_missing_version(self):
        """load_state() rejects data without version field."""
        engine = _make_engine(":: Start\nHello")
        with pytest.raises(ValueError, match="missing version"):
            engine.load_state({"current_passage_id": "Start"})

    def test_load_validates_unknown_passage(self):
        """load_state() rejects data referencing nonexistent passages."""
        engine = _make_engine(":: Start\nHello")
        with pytest.raises(ValueError, match="unknown passage"):
            engine.load_state({
                "version": "0.1.0",
                "current_passage_id": "NonExistent",
                "state": {},
            })

    def test_load_clears_undo_redo_stacks(self):
        """Loading a save clears both undo and redo stacks."""
        engine = _make_engine(
            ":: Start\nHello\n+ [Go] -> End\n\n:: End\nDone\n+ [Back] -> Start"
        )
        engine.choose(0)  # creates undo entry
        assert engine.can_undo()

        save_data = engine.save_state()
        engine.load_state(save_data)
        assert not engine.can_undo()
        assert not engine.can_redo()


# ── Undo/Redo via StateManager ──


class TestUndoRedoStateManager:
    """Tests for undo/redo through the StateManager interface."""

    def test_snapshot_enables_undo(self):
        """After snapshot + state change, undo restores."""
        engine = _make_engine(
            ":: Start\n~ x = 1\nHello\n+ [Go] -> End\n\n:: End\n~ x = 99\nDone"
        )
        assert engine.state["x"] == 1
        engine.choose(0)  # auto-snapshots
        assert engine.state["x"] == 99
        engine.undo()
        assert engine.state["x"] == 1

    def test_undo_then_redo(self):
        """Undo followed by redo restores the undone state."""
        engine = _make_engine(
            ":: Start\n~ x = 1\nHello\n+ [Go] -> End\n\n:: End\n~ x = 99\nDone"
        )
        engine.choose(0)
        engine.undo()
        assert engine.state["x"] == 1
        engine.redo()
        assert engine.state["x"] == 99

    def test_can_undo_false_initially(self):
        """No undo available at start."""
        engine = _make_engine(":: Start\nHello")
        assert not engine.can_undo()

    def test_can_redo_false_initially(self):
        """No redo available at start."""
        engine = _make_engine(":: Start\nHello")
        assert not engine.can_redo()

    def test_undo_stack_bounded(self):
        """Undo stack respects maxlen."""
        engine = _make_engine(":: Start\nHello")
        assert engine.undo_stack.maxlen == 50


class TestImportPaths:
    """Tests for StateManager import accessibility."""

    def test_import_from_state_module(self):
        """StateManager is importable from bardic.runtime.state."""
        from bardic.runtime.state import StateManager as SM
        assert SM is StateManager

    def test_import_from_runtime_package(self):
        """StateManager is importable from bardic.runtime."""
        from bardic.runtime import StateManager as SM
        assert SM is StateManager
