"""Tests for the _visits passage counter and _turns choice counter."""

import pytest
from bardic.compiler.compiler import BardCompiler
from bardic.runtime.engine import BardEngine


def make_engine(source: str) -> BardEngine:
    """Compile a .bard source string and return a ready engine."""
    compiler = BardCompiler()
    story_data = compiler.compile_string(source)
    return BardEngine(story_data)


BASIC_STORY = """
:: Start
Hello!
+ [Go to tavern] -> Tavern
+ [Stay here] -> Start

:: Tavern
Welcome to the tavern!
+ [Go back] -> Start
+ [Order ale] -> Tavern
"""


class TestVisits:
    """Tests for _visits passage visit counting."""

    def test_initial_passage_counted(self):
        """The starting passage should have visit count 1 after engine init."""
        engine = make_engine(BASIC_STORY)
        assert engine.state["_visits"]["Start"] == 1

    def test_unvisited_passage_not_in_dict(self):
        """Passages not yet visited should not appear in _visits."""
        engine = make_engine(BASIC_STORY)
        assert "Tavern" not in engine.state["_visits"]

    def test_visit_increments_on_navigation(self):
        """Choosing a passage should increment its visit count."""
        engine = make_engine(BASIC_STORY)
        engine.choose(0)  # Go to tavern
        assert engine.state["_visits"]["Tavern"] == 1

    def test_revisit_increments(self):
        """Revisiting a passage should increment the count again."""
        engine = make_engine(BASIC_STORY)
        engine.choose(0)  # Go to tavern
        engine.choose(1)  # Order ale (revisit Tavern)
        assert engine.state["_visits"]["Tavern"] == 2

    def test_multiple_passages_tracked(self):
        """All visited passages should be tracked independently."""
        engine = make_engine(BASIC_STORY)
        engine.choose(0)  # Start -> Tavern
        engine.choose(0)  # Tavern -> Start
        assert engine.state["_visits"]["Start"] == 2
        assert engine.state["_visits"]["Tavern"] == 1

    def test_visits_accessible_in_expressions(self):
        """_visits should be usable in story expressions."""
        engine = make_engine("""
:: Start
Visit count: {_visits.get("Start", 0)}
+ [Loop] -> Start
""")
        output = engine.current()
        assert "Visit count: 1" in output.content

    def test_visits_accessible_in_conditions(self):
        """_visits should be usable in choice conditions."""
        engine = make_engine("""
:: Start
Hello!
+ [First visit only] -> End
+ {_visits.get("Start", 0) >= 2} [Welcome back!] -> End

:: End
Done.
""")
        # First visit: only "First visit only" should show
        output = engine.current()
        assert len(output.choices) == 1
        assert output.choices[0]["text"] == "First visit only"

    def test_visits_survives_undo(self):
        """Undo should restore previous visit counts."""
        engine = make_engine(BASIC_STORY)
        engine.choose(0)  # Start -> Tavern (Tavern visits = 1)
        engine.choose(1)  # Order ale (Tavern visits = 2)

        engine.undo()
        assert engine.state["_visits"]["Tavern"] == 1

    def test_visits_survives_redo(self):
        """Redo should restore forward visit counts."""
        engine = make_engine(BASIC_STORY)
        engine.choose(0)  # Start -> Tavern
        engine.choose(1)  # Order ale (Tavern visits = 2)

        engine.undo()
        assert engine.state["_visits"]["Tavern"] == 1

        engine.redo()
        assert engine.state["_visits"]["Tavern"] == 2

    def test_visits_with_jumps(self):
        """Passages reached via jumps should also be counted."""
        engine = make_engine("""
:: Start
+ [Go] -> Middle

:: Middle
-> End

:: End
Done.
""")
        engine.choose(0)  # Start -> Middle -> End (via jump)
        assert engine.state["_visits"]["Middle"] == 1
        assert engine.state["_visits"]["End"] == 1


class TestTurns:
    """Tests for _turns choice counter."""

    def test_initial_turns_is_zero(self):
        """Turns should start at 0."""
        engine = make_engine(BASIC_STORY)
        assert engine.state["_turns"] == 0

    def test_turns_increments_on_choose(self):
        """Each choose() call should increment _turns by 1."""
        engine = make_engine(BASIC_STORY)
        engine.choose(0)  # Turn 1
        assert engine.state["_turns"] == 1
        engine.choose(0)  # Turn 2
        assert engine.state["_turns"] == 2

    def test_turns_accessible_in_expressions(self):
        """_turns should be usable in story expressions."""
        engine = make_engine("""
:: Start
Turns: {_turns}
+ [Next] -> Start
""")
        output = engine.current()
        assert "Turns: 0" in output.content

        output = engine.choose(0)
        assert "Turns: 1" in output.content

    def test_turns_accessible_in_conditions(self):
        """_turns should be usable in choice conditions."""
        engine = make_engine("""
:: Start
Hello!
+ [Continue] -> Start
+ {_turns >= 3} [I've been here a while...] -> End

:: End
Done.
""")
        # Turns 0, 1, 2: only "Continue" shows
        for _ in range(3):
            output = engine.current()
            assert len(output.choices) == 1
            engine.choose(0)

        # Turn 3: both choices show
        output = engine.current()
        assert len(output.choices) == 2

    def test_turns_not_incremented_by_goto(self):
        """goto() should NOT increment turns — only choose() does."""
        engine = make_engine(BASIC_STORY)
        engine.goto("Tavern")  # Direct navigation, not a player choice
        assert engine.state["_turns"] == 0

    def test_turns_survives_undo(self):
        """Undo should restore previous turn count."""
        engine = make_engine(BASIC_STORY)
        engine.choose(0)  # Turn 1
        engine.choose(0)  # Turn 2
        engine.choose(0)  # Turn 3

        engine.undo()
        assert engine.state["_turns"] == 2

    def test_turns_survives_redo(self):
        """Redo should restore forward turn count."""
        engine = make_engine(BASIC_STORY)
        engine.choose(0)  # Turn 1
        engine.choose(0)  # Turn 2

        engine.undo()
        assert engine.state["_turns"] == 1

        engine.redo()
        assert engine.state["_turns"] == 2
