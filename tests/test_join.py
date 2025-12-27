"""Test the Bardic @join directive system."""

import pytest
from bardic.runtime.engine import BardEngine


@pytest.fixture
def basic_join_story():
    """A story with basic @join functionality."""
    return {
        "version": "0.1.0",
        "initial_passage": "Start",
        "passages": {
            "Start": {
                "id": "Start",
                "content": [
                    {"type": "text", "value": "Choose your fruit."},
                    {"type": "text", "value": "\n"},
                    {"type": "join_marker", "id": 0},
                    {"type": "text", "value": "You chose the "},
                    {"type": "expression", "code": "choice"},
                    {"type": "text", "value": "."},
                    {"type": "text", "value": "\n"},
                ],
                "choices": [
                    {
                        "text": [{"type": "text", "value": "Apple"}],
                        "target": "@join",
                        "sticky": True,
                        "section": 0,
                        "block_content": [
                            {"type": "text", "value": "You pick the apple."},
                            {"type": "text", "value": "\n"},
                            {"type": "python_statement", "code": "choice = 'apple'"},
                        ],
                    },
                    {
                        "text": [{"type": "text", "value": "Pear"}],
                        "target": "@join",
                        "sticky": True,
                        "section": 0,
                        "block_content": [
                            {"type": "text", "value": "You pick the pear."},
                            {"type": "text", "value": "\n"},
                            {"type": "python_statement", "code": "choice = 'pear'"},
                        ],
                    },
                    {
                        "text": [{"type": "text", "value": "Continue"}],
                        "target": "End",
                        "sticky": True,
                        "section": 1,
                    },
                ],
                "execute": [],
            },
            "End": {
                "id": "End",
                "content": [{"type": "text", "value": "Done."}],
                "choices": [],
                "execute": [],
            },
        },
    }


class TestJoinBasics:
    """Test basic @join functionality."""

    def test_initial_shows_section_0_choices(self, basic_join_story):
        """Initially only section 0 choices should be visible."""
        engine = BardEngine(basic_join_story)
        output = engine.current()

        choices = [c["text"] for c in output.choices]
        assert "Apple" in choices
        assert "Pear" in choices
        assert "Continue" not in choices  # Section 1

    def test_initial_content_stops_at_join_marker(self, basic_join_story):
        """Initial content should stop at @join marker."""
        engine = BardEngine(basic_join_story)
        output = engine.current()

        assert "Choose your fruit" in output.content
        assert "You chose the" not in output.content  # After @join

    def test_join_choice_renders_block_content(self, basic_join_story):
        """Choosing a @join option renders its block content."""
        engine = BardEngine(basic_join_story)
        output = engine.choose(0)  # Apple

        assert "You pick the apple" in output.content

    def test_join_choice_executes_block_variables(self, basic_join_story):
        """Variables set in @join block should persist."""
        engine = BardEngine(basic_join_story)
        engine.choose(0)  # Apple

        assert engine.state.get("choice") == "apple"

    def test_join_choice_shows_post_join_content(self, basic_join_story):
        """After @join choice, content after marker should appear."""
        engine = BardEngine(basic_join_story)
        output = engine.choose(0)  # Apple

        assert "You chose the apple" in output.content

    def test_join_choice_advances_to_next_section(self, basic_join_story):
        """After @join, next section's choices should appear."""
        engine = BardEngine(basic_join_story)
        output = engine.choose(0)  # Apple

        choices = [c["text"] for c in output.choices]
        assert "Continue" in choices
        assert "Apple" not in choices  # Section 0 choices gone


class TestJoinWithParsing:
    """Test @join with compiled stories."""

    def test_basic_join_compiles(self, compile_string):
        """Basic @join syntax should compile correctly."""
        story = compile_string("""
:: Start
Pick one.

+ [A] -> @join
    Chose A.
    ~ picked = "A"

+ [B] -> @join
    Chose B.
    ~ picked = "B"

@join
You picked {picked}.
+ [Done] -> End

:: End
Done.
""")
        # Check structure
        start = story["passages"]["Start"]
        assert len(start["choices"]) == 3  # A, B, Done

        # Check @join choices have block_content
        a_choice = start["choices"][0]
        assert a_choice["target"] == "@join"
        assert "block_content" in a_choice
        assert a_choice["section"] == 0

        # Check Done is section 1
        done_choice = start["choices"][2]
        assert done_choice["section"] == 1

    def test_join_marker_creates_token(self, compile_string):
        """@join marker should create join_marker token."""
        story = compile_string("""
:: Start
Before.
@join
After.
+ [End] -> End

:: End
Done.
""")
        content = story["passages"]["Start"]["content"]
        join_markers = [t for t in content if t.get("type") == "join_marker"]
        assert len(join_markers) == 1
        assert join_markers[0]["id"] == 0


class TestMultipleJoins:
    """Test multiple sequential @join markers."""

    def test_two_join_sections(self, compile_string):
        """Multiple @join markers create multiple sections."""
        story = compile_string("""
:: Start
Round 1.

+ [A1] -> @join
    ~ r1 = "A"

+ [B1] -> @join
    ~ r1 = "B"

@join
Round 1 done.
Round 2.

+ [A2] -> @join
    ~ r2 = "A"

+ [B2] -> @join
    ~ r2 = "B"

@join
All done.
+ [End] -> End

:: End
Done.
""")
        engine = BardEngine(story)

        # Round 1 choices
        choices = [c["text"] for c in engine.current().choices]
        assert "A1" in choices
        assert "A2" not in choices

        # Choose round 1
        engine.choose(0)
        choices = [c["text"] for c in engine.current().choices]
        assert "A2" in choices
        assert "A1" not in choices

        # Choose round 2
        output = engine.choose(1)  # B2
        assert engine.state.get("r2") == "B"
        choices = [c["text"] for c in output.choices]
        assert "End" in choices


class TestJoinWithConditions:
    """Test @join with conditional choices."""

    def test_conditional_join_choices(self, compile_string):
        """Conditional @join choices should filter correctly."""
        story = compile_string("""
:: Start
~ has_key = True
~ has_sword = False
Pick tool.

+ {has_key} [Use key] -> @join
    Key used.

+ {has_sword} [Use sword] -> @join
    Sword used.

+ [Nothing] -> @join
    Nothing used.

@join
Done.
+ [End] -> End

:: End
Bye.
""")
        engine = BardEngine(story)
        choices = [c["text"] for c in engine.current().choices]

        assert "Use key" in choices
        assert "Nothing" in choices
        assert "Use sword" not in choices  # has_sword is False


class TestJoinWithSticky:
    """Test @join with one-time (non-sticky) choices."""

    def test_one_time_join_choice_disappears(self, compile_string):
        """One-time @join choices should not reappear."""
        story = compile_string("""
:: Start
~ count = 0
Pick.

* [One-time] -> @join
    ~ count = count + 1

+ [Repeatable] -> @join
    ~ count = count + 1

@join
Count: {count}
+ [Again] -> Start
+ [End] -> End

:: End
Done.
""")
        engine = BardEngine(story)

        # Both visible initially
        choices = [c["text"] for c in engine.current().choices]
        assert "One-time" in choices
        assert "Repeatable" in choices

        # Use one-time
        engine.choose(0)
        engine.choose(0)  # Again -> Start

        # One-time gone
        choices = [c["text"] for c in engine.current().choices]
        assert "One-time" not in choices
        assert "Repeatable" in choices


class TestJoinWithUndoRedo:
    """Test @join interaction with undo/redo."""

    def test_undo_restores_section_index(self, compile_string):
        """Undo should restore the section index."""
        story = compile_string("""
:: Start
~ x = 0
Pick.

+ [Set 1] -> @join
    ~ x = 1

+ [Set 2] -> @join
    ~ x = 2

@join
x = {x}
+ [End] -> End

:: End
Done.
""")
        engine = BardEngine(story)

        # Make choice
        engine.choose(0)
        assert engine.state.get("x") == 1

        # Undo
        engine.undo()
        assert engine.state.get("x") == 0

        # Should be back at section 0
        choices = [c["text"] for c in engine.current().choices]
        assert "Set 1" in choices
        assert "End" not in choices

    def test_redo_restores_after_undo(self, compile_string):
        """Redo should restore state after undo."""
        story = compile_string("""
:: Start
~ x = 0
+ [Set 1] -> @join
    ~ x = 1
@join
Done.
+ [End] -> End
:: End
Bye.
""")
        engine = BardEngine(story)
        engine.choose(0)
        engine.undo()
        engine.redo()

        assert engine.state.get("x") == 1


class TestJoinWithHooks:
    """Test @join with hooks system."""

    def test_hook_in_join_block(self, compile_string):
        """Hooks registered in @join blocks should work."""
        story = compile_string("""
:: Start
~ counter = 0
Pick.

+ [Register] -> @join
    @hook turn_end Counter

+ [Skip] -> @join
    Skip.

@join
Counter: {counter}
+ [Continue] -> Room

:: Counter
~ counter = counter + 1

:: Room
Room.
+ [Stay] -> Room
""")
        engine = BardEngine(story)

        # Register hook
        engine.choose(0)
        assert engine.state.get("counter") == 1  # Hook fired

        # Continue
        engine.choose(0)
        assert engine.state.get("counter") == 2  # Hook fired again


class TestMixedJoinAndRegular:
    """Test passages with both @join and regular choices."""

    def test_regular_choice_exits_join_flow(self, compile_string):
        """Regular choice should navigate away, ignoring @join."""
        story = compile_string("""
:: Start
Options.

+ [Stay] -> @join
    Staying.

+ [Leave] -> Left

@join
Still here.
+ [Continue] -> End

:: Left
You left.

:: End
Done.
""")
        engine = BardEngine(story)

        # Choose "Leave" (regular choice)
        engine.choose(1)

        assert engine.current_passage_id == "Left"
        assert "You left" in engine.current().content
