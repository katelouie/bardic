"""
State management for the Bardic runtime engine.

Handles undo/redo snapshots, save/load serialization, and save metadata.
The StateManager takes an engine reference and manages all state persistence.
"""

import json
from collections import deque
from datetime import datetime
from typing import Any, TYPE_CHECKING

from bardic.runtime.types import GameSnapshot

if TYPE_CHECKING:
    from bardic.runtime.engine import BardEngine


class StateManager:
    """Manages undo/redo stacks and save/load serialization.

    Takes a reference to the engine for snapshot capture/restore
    and access to story metadata during save/load.

    Usage:
        state_mgr = StateManager(engine, max_undo=50)
        state_mgr.snapshot()       # capture before a choice
        state_mgr.undo()           # restore previous state
        save_data = state_mgr.save_state()  # serialize for JSON
    """

    def __init__(self, engine: "BardEngine", max_undo: int = 50):
        self.engine = engine
        self.undo_stack: deque[GameSnapshot] = deque(maxlen=max_undo)
        self.redo_stack: list[GameSnapshot] = []

    # ── Undo/Redo ──

    def snapshot(self) -> None:
        """Capture current state to the undo stack.

        Call this BEFORE making any state changes. The snapshot captures
        the state at the moment before a choice is made, so undo returns
        the player to that decision point.
        """
        snapshot = GameSnapshot.from_engine(self.engine)
        self.undo_stack.append(snapshot)

    def undo(self) -> bool:
        """Restore previous state from undo stack.

        Moves current state to redo stack before restoring, so the player
        can redo if they change their mind.

        Returns:
            True if undo was successful, False if nothing to undo.
        """
        if not self.undo_stack:
            return False

        # Save current state to redo stack before restoring
        current = GameSnapshot.from_engine(self.engine)
        self.redo_stack.append(current)

        # Restore previous state
        previous = self.undo_stack.pop()
        previous.restore_to(self.engine)

        # Re-render the restored passage (updates _current_output cache)
        self.engine._current_output = self.engine._render_passage(
            self.engine.current_passage_id
        )

        return True

    def redo(self) -> bool:
        """Restore next state from redo stack.

        Returns:
            True if redo was successful, False if nothing to redo.
        """
        if not self.redo_stack:
            return False

        # Save current state to undo stack before restoring
        current = GameSnapshot.from_engine(self.engine)
        self.undo_stack.append(current)

        # Restore next state
        next_state = self.redo_stack.pop()
        next_state.restore_to(self.engine)

        # Re-render the restored passage
        self.engine._current_output = self.engine._render_passage(
            self.engine.current_passage_id
        )

        return True

    def can_undo(self) -> bool:
        """Check if undo is available (for UI button state)."""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available (for UI button state)."""
        return len(self.redo_stack) > 0

    # ── Save/Load ──

    def save_state(self) -> dict[str, Any]:
        """Serialize engine state to a dictionary that can be saved to JSON.

        Returns a complete snapshot of the current game state including:
        - Current passage ID
        - All variables in state
        - Used one-time choices
        - Story metadata for validation

        Returns:
            Dictionary containing all state needed to restore the game

        Example:
            state = engine.save_state()
            with open('save.json', 'w') as f:
                json.dump(state, f)
        """
        engine = self.engine
        story_metadata = engine.story.get("metadata", {})

        return {
            "version": "0.1.0",  # Save format version
            "story_version": story_metadata.get("version", "unknown"),
            "story_name": story_metadata.get("title", "unknown"),
            "story_id": story_metadata.get("story_id", "unknown"),
            "timestamp": self._get_timestamp(),
            "current_passage_id": engine.current_passage_id,
            "previous_passage_id": engine._previous_passage_id,
            "state": self._serialize_state(engine.state),
            "used_choices": list(engine.used_choices),
            "metadata": {
                "passage_count": len(engine.passages),
                "initial_passage": engine.story["initial_passage"],
            },
            "hooks": engine.hook_manager.hooks,
        }

    def load_state(self, save_data: dict[str, Any]) -> None:
        """Restore engine state from a saved dictionary.

        Validates the save data before loading to ensure compatibility.

        Args:
            save_data: Dictionary from save_state()

        Raises:
            ValueError: If save data is invalid or incompatible

        Example:
            with open('save.json') as f:
                save_data = json.load(f)
            engine.load_state(save_data)
        """
        engine = self.engine

        # Validate save format
        if not isinstance(save_data, dict):
            raise ValueError("Save data must be a dictionary")

        if "version" not in save_data:
            raise ValueError("Save data missing version field")

        # Validate story compatibility using metadata
        story_metadata = engine.story.get("metadata", {})

        saved_story_name = save_data.get("story_name", "unknown")
        current_story_name = story_metadata.get("title", "unknown")

        saved_story_id = save_data.get("story_id", "unknown")
        current_story_id = story_metadata.get("story_id", "unknown")

        # Check both story_id (primary) and story_name (secondary) for compatibility
        if saved_story_id != "unknown" and current_story_id != "unknown":
            if saved_story_id != current_story_id:
                print(
                    f"Warning: Save is from a different story ID: '{saved_story_id}' vs '{current_story_id}'"
                )
        elif saved_story_name != current_story_name and saved_story_name != "unknown":
            print(
                f"Warning: Save is from a different story: '{saved_story_name}' vs '{current_story_name}'"
            )

        # Validate passage exists
        target_passage = save_data.get("current_passage_id", "Start")
        if target_passage not in engine.passages:
            raise ValueError(
                f"Save data references unknown passage: '{target_passage}'\n"
                f"Available passages: {', '.join(sorted(engine.passages.keys())[:5])}..."
            )

        # Restore state — mutate in place to preserve references held by subsystems
        engine.state.clear()
        engine.state.update(self._deserialize_state(save_data.get("state", {})))
        engine.used_choices.clear()
        engine.used_choices.update(save_data.get("used_choices", []))

        # Clear undo/redo stacks on load (fresh start, new session)
        self.undo_stack.clear()
        self.redo_stack.clear()

        # Restore hooks
        engine.hook_manager.restore(save_data.get("hooks", {}))

        # Navigate to saved passage (this re-renders with restored state)
        engine.goto(target_passage)

        # Restore previous passage AFTER goto (goto would overwrite it)
        engine._previous_passage_id = save_data.get("previous_passage_id")

    # ── Serialization ──

    def _serialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Serialize state dictionary for JSON storage.

        Delegates all value serialization to _serialize_value for consistency.
        This ensures custom serialization methods and recursive handling work
        for all values, regardless of nesting level.

        Args:
            state: Raw state dictionary

        Returns:
            JSON-serializable dictionary
        """
        serialized = {}
        for key, value in state.items():
            serialized[key] = self._serialize_value(value)
        return serialized

    def _serialize_value(self, value: Any) -> Any:
        """Serialize a single value for JSON storage.

        Priority order:
        0. Skip classes/types and callables (they shouldn't be in save files)
        1. Check for custom to_save_dict() method (explicit serialization)
        2. Try direct JSON serialization (primitives)
        3. Collections (lists, tuples, dicts) - recurse
        4. Objects with __dict__
        5. Fallback to string representation
        """
        # Priority 0: Skip classes/types and callables - they shouldn't be serialized
        # Functions (like create_session, get_artifact) have __dict__ and would
        # fall through to Priority 4, getting serialized as dicts. On load,
        # they can't be restored as callables, breaking the game state.
        if isinstance(value, type) or callable(value):
            return None

        # Priority 1: Custom serialization method
        if hasattr(value, "to_save_dict") and callable(getattr(value, "to_save_dict")):
            return {
                "_type": type(value).__name__,
                "_module": type(value).__module__,
                "_data": value.to_save_dict(),
                "_custom": True,  # Flag that this used custom serialization
            }

        # Priority 2: Direct JSON serialization (primitives)
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            pass

        # Priority 3: Collections - recurse for nested structures
        if isinstance(value, list):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, tuple):
            # Store tuples as lists (JSON doesn't have tuples)
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            # Recurse through dict values
            return {k: self._serialize_value(v) for k, v in value.items()}

        # Priority 4: Object with __dict__
        if hasattr(value, "__dict__"):
            return {
                "_type": type(value).__name__,
                "_module": type(value).__module__,
                "_data": {
                    # Recurse for nested objects in attributes
                    k: self._serialize_value(v)
                    for k, v in value.__dict__.items()
                    if not k.startswith("_")
                },
            }

        # Priority 5: Fallback to string
        print(f"Warning: Serializing {type(value).__name__} as string representation")
        return {"_type": "string_repr", "_value": str(value)}

    def _deserialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """Deserialize state dictionary from JSON storage.

        Delegates all value deserialization to _deserialize_value for consistency.
        This ensures custom deserialization methods and recursive handling work
        for all values, regardless of nesting level.

        Args:
            state: Serialized state dictionary

        Returns:
            Restored state dictionary
        """
        deserialized = {}
        for key, value in state.items():
            deserialized[key] = self._deserialize_value(value)
        return deserialized

    def _deserialize_value(self, value: Any) -> Any:
        """Deserialize a single value from JSON storage.

        Priority Order:
        1. Handle primitives (return as-is)
        2. Handle collections (recurse)
        3. Handle objects with custom from_save_dict() (explicit deserialization)
        4. Handle objects with __new__ + __dict__ (automatic deserialization)
        5. Return as dict if class not available
        """
        # Priority 1: Primitives - return as-is
        if not isinstance(value, (dict, list)):
            return value

        # Priority 2: Collections - recurse
        if isinstance(value, list):
            return [self._deserialize_value(v) for v in value]

        # Priority 3-5: Objects with _type metadata
        if not isinstance(value, dict) or "_type" not in value:
            # Plain dict without _type - recurse through values
            if isinstance(value, dict):
                return {k: self._deserialize_value(v) for k, v in value.items()}
            return value

        obj_type = value["_type"]
        obj_data = value.get("_data", {})

        # Special case: string representation
        if obj_type == "string_repr":
            return value.get("_value", "")

        # Try to get class from context
        context = self.engine.context
        if obj_type not in context:
            # Class not available - recurse through data dict
            print(f"Warning: Class '{obj_type}' not in context, keeping as dict")
            return {k: self._deserialize_value(v) for k, v in obj_data.items()}

        cls = context[obj_type]

        # Priority 3: Custom deserialization method
        if hasattr(cls, "from_save_dict") and callable(getattr(cls, "from_save_dict")):
            try:
                return cls.from_save_dict(obj_data)
            except Exception as e:
                print(f"Warning: Custom deserialization failed for {obj_type}: {e}")
                # Fall through to automatic method

        # Priority 4: Automatic deserialization using __new__
        try:
            obj = cls.__new__(cls)
            if hasattr(obj, "__dict__"):
                # Recursively deserialize nested values in obj_data
                deserialized_data = {
                    k: self._deserialize_value(v) for k, v in obj_data.items()
                }
                obj.__dict__.update(deserialized_data)
            return obj
        except Exception as e:
            print(f"Warning: Failed to deserialize {obj_type}: {e}")
            # Recurse through data dict as fallback
            return {k: self._deserialize_value(v) for k, v in obj_data.items()}

    # ── Metadata ──

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()

    def get_save_metadata(self) -> dict[str, Any]:
        """Get metadata about the current save state without full serialization.

        Useful for displaying save slot information without loading the full save.

        Returns:
            Dictionary with save metadata (passage, timestamp, etc.)
        """
        return {
            "current_passage": self.engine.current_passage_id,
            "timestamp": self._get_timestamp(),
            "story_name": self.engine.story.get("name", "unknown"),
            "has_choices": self.engine.has_choices(),
        }
