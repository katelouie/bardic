"""Test the Bardic runtime engine."""

import pytest
from bardic.runtime.engine import BardEngine


class TestBasicNavigation:
    """Test basic story navigation features."""

    def test_engine_initializes_at_start(self, simple_story):
        """Engine should initialize at the initial_passage."""
        # When: We create an engine
        engine = BardEngine(simple_story)

        # Then: It should be at the Start passage
        output = engine.current()
        assert output.passage_id == "Start"
        assert "You are at the start" in output.content

    def test_navigate_with_choose(self, simple_story):
        """Choosing a choice should navigate to the target passage."""
        # Given: An engine at Start
        engine = BardEngine(simple_story)

        # When: We choose the first choice
        output = engine.choose(0)

        # Then: We should be at Second passage
        assert output.passage_id == "Second"
        assert "second passage" in output.content

    def test_navigate_with_goto(self, simple_story):
        """goto() should jump directly to a passage."""
        # Given: An engine at Start
        engine = BardEngine(simple_story)

        # When: We goto Second
        output = engine.goto("Second")

        # Then: We should be at Second
        assert output.passage_id == "Second"
        assert "second passage" in output.content


class TestErrorHandling:
    """Test that the engine handles errors correctly."""

    def test_goto_nonexistent_passage_raises_error(self, simple_story):
        """goto() should raise ValueError for non-existent passages."""
        # Given: An engine
        engine = BardEngine(simple_story)

        # When/Then: Trying to goto a non-existent passage should raise
        with pytest.raises(ValueError, match="unknown passage"):
            engine.goto("NonExistentPassage")

    def test_choose_invalid_index_raises_error(self, simple_story):
        """choose() should raise IndexError for invalid choice indices."""
        # Given: An engine at Start (which has 1 choice)
        engine = BardEngine(simple_story)

        # When/Then: Choosing index 999 should raise IndexError
        with pytest.raises(IndexError, match="out of range"):
            engine.choose(999)

    def test_choose_negative_index_raises_error(self, simple_story):
        """choose() should raise IndexError for negative indices."""
        engine = BardEngine(simple_story)

        with pytest.raises(IndexError):
            engine.choose(-1)


class TestStoryInfo:
    """Test the get_story_info() method."""

    def test_get_story_info_returns_metadata(self, simple_story):
        """get_story_info() should return story metadata."""
        # Given: An engine
        engine = BardEngine(simple_story)

        # When: We get story info
        info = engine.get_story_info()

        # Then: It should contain expected fields
        assert info["version"] == "0.1.0"
        assert info["passage_count"] == 2
        assert info["initial_passage"] == "Start"
        assert info["current_passage"] == "Start"
