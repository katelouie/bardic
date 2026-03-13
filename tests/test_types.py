"""Tests for bardic.runtime.types — PassageOutput and GameSnapshot."""

from bardic.runtime.types import PassageOutput, GameSnapshot
from bardic.runtime.engine import BardEngine
from bardic.compiler.compiler import BardCompiler


# ── PassageOutput ──


class TestPassageOutput:
    """Tests for the PassageOutput dataclass."""

    def test_basic_creation(self):
        """Create a PassageOutput with required fields."""
        output = PassageOutput(
            content="Hello world",
            choices=[{"text": "Continue", "target": "Next"}],
            passage_id="Start",
        )
        assert output.content == "Hello world"
        assert output.passage_id == "Start"
        assert len(output.choices) == 1
        assert output.choices[0]["text"] == "Continue"

    def test_defaults_initialized(self):
        """Optional fields default to empty lists, not None."""
        output = PassageOutput(content="", choices=[], passage_id="X")
        assert output.render_directives == []
        assert output.input_directives == []
        assert output.jump_target is None

    def test_none_directives_become_empty_lists(self):
        """Explicitly passing None for directives gets post_init'd to []."""
        output = PassageOutput(
            content="",
            choices=[],
            passage_id="X",
            render_directives=None,
            input_directives=None,
        )
        assert output.render_directives == []
        assert output.input_directives == []

    def test_explicit_directives_preserved(self):
        """Passing actual directive lists doesn't get overwritten."""
        render = [{"name": "card_spread", "data": {}}]
        inputs = [{"name": "player_name", "label": "Name"}]
        output = PassageOutput(
            content="",
            choices=[],
            passage_id="X",
            render_directives=render,
            input_directives=inputs,
        )
        assert output.render_directives == render
        assert output.input_directives == inputs

    def test_jump_target(self):
        """Jump target field works."""
        output = PassageOutput(content="", choices=[], passage_id="X", jump_target="Death")
        assert output.jump_target == "Death"

    def test_import_from_engine_module(self):
        """PassageOutput is importable from its original location."""
        from bardic.runtime.engine import PassageOutput as PO

        assert PO is PassageOutput

    def test_import_from_runtime_package(self):
        """PassageOutput is importable from the runtime package."""
        from bardic.runtime import PassageOutput as PO

        assert PO is PassageOutput

    def test_import_from_top_level(self):
        """PassageOutput is importable from the top-level bardic package."""
        from bardic import PassageOutput as PO

        assert PO is PassageOutput


# ── GameSnapshot ──


class TestGameSnapshot:
    """Tests for the GameSnapshot dataclass."""

    def _make_engine(self, story_str: str) -> BardEngine:
        """Helper to compile and create an engine from a .bard string."""
        compiler = BardCompiler()
        story_data = compiler.compile_string(story_str)
        return BardEngine(story_data)

    def test_basic_creation(self):
        """Create a GameSnapshot with all fields."""
        snap = GameSnapshot(
            current_passage="Start",
            previous_passage=None,
            state={"hp": 100},
            used_choices=set(),
            hooks={},
            join_section_index={},
        )
        assert snap.current_passage == "Start"
        assert snap.state["hp"] == 100

    def test_from_engine(self):
        """GameSnapshot.from_engine captures the engine's current state."""
        engine = self._make_engine(":: Start\nHello\n+ [Go] -> End\n\n:: End\nDone")
        snap = GameSnapshot.from_engine(engine)
        assert snap.current_passage == "Start"
        assert snap.previous_passage is None
        assert "_visits" in snap.state
        assert isinstance(snap.used_choices, set)
        assert isinstance(snap.hooks, dict)
        assert isinstance(snap.join_section_index, dict)

    def test_from_engine_deep_copies_state(self):
        """Snapshot state is a deep copy — mutating engine doesn't affect it."""
        engine = self._make_engine(":: Start\n~ items = [1, 2, 3]\nHello")
        snap = GameSnapshot.from_engine(engine)

        # Mutate engine state after snapshot
        engine.state["items"].append(4)

        # Snapshot should be unchanged
        assert snap.state["items"] == [1, 2, 3]

    def test_restore_to_engine(self):
        """Restoring a snapshot resets the engine to that state."""
        engine = self._make_engine(
            ":: Start\n~ x = 10\nHello\n+ [Go] -> End\n\n:: End\n~ x = 99\nDone"
        )

        # Snapshot at Start
        snap = GameSnapshot.from_engine(engine)
        assert engine.state["x"] == 10

        # Navigate to End
        engine.choose(0)
        assert engine.state["x"] == 99
        assert engine.current_passage_id == "End"

        # Restore snapshot
        snap.restore_to(engine)
        assert engine.state["x"] == 10
        assert engine.current_passage_id == "Start"

    def test_snapshot_captures_used_choices(self):
        """One-time choices are tracked in the snapshot."""
        engine = self._make_engine(
            ":: Start\n* [One-time] -> End\n+ [Sticky] -> End\n\n:: End\nDone"
        )
        snap_before = GameSnapshot.from_engine(engine)
        assert len(snap_before.used_choices) == 0

        # Use the one-time choice
        engine.choose(0)
        snap_after = GameSnapshot.from_engine(engine)
        assert len(snap_after.used_choices) == 1

    def test_snapshot_captures_hooks(self):
        """Hook registrations are captured in the snapshot."""
        engine = self._make_engine(
            ":: Start\n@hook turn_end Ticker\n+ [Go] -> Next\n\n:: Ticker\n~ x = 1\n\n:: Next\nDone"
        )
        snap = GameSnapshot.from_engine(engine)
        assert "turn_end" in snap.hooks
        assert "Ticker" in snap.hooks["turn_end"]

    def test_import_from_top_level(self):
        """GameSnapshot is importable from the top-level bardic package."""
        from bardic import GameSnapshot as GS

        assert GS is GameSnapshot

    def test_import_from_runtime_package(self):
        """GameSnapshot is importable from the runtime package."""
        from bardic.runtime import GameSnapshot as GS

        assert GS is GameSnapshot
