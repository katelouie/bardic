"""Test the @prev target functionality for navigating to the previous passage."""

import pytest
from bardic.runtime.engine import BardEngine


@pytest.fixture
def prev_story():
    """A story with @prev navigation for testing."""
    return {
        "version": "0.1.0",
        "initial_passage": "Start",
        "passages": {
            "Start": {
                "id": "Start",
                "content": [{"type": "text", "value": "Welcome!"}],
                "choices": [
                    {"text": "Go to Menu", "target": "Menu"},
                    {"text": "Go to Shop", "target": "Shop"},
                ],
                "execute": [],
            },
            "Menu": {
                "id": "Menu",
                "content": [{"type": "text", "value": "This is the menu."}],
                "choices": [
                    {"text": "Go back", "target": "@prev"},
                    {"text": "Go to Shop", "target": "Shop"},
                ],
                "execute": [],
            },
            "Shop": {
                "id": "Shop",
                "content": [{"type": "text", "value": "Welcome to the shop!"}],
                "choices": [
                    {"text": "Go back", "target": "@prev"},
                    {"text": "Go to Menu", "target": "Menu"},
                ],
                "execute": [],
            },
        },
    }


@pytest.fixture
def jump_chain_story():
    """A story with automatic jumps to test @prev with jump chains."""
    return {
        "version": "0.1.0",
        "initial_passage": "Start",
        "passages": {
            "Start": {
                "id": "Start",
                "content": [{"type": "text", "value": "Start passage"}],
                "choices": [{"text": "Go to Hub", "target": "Hub"}],
                "execute": [],
            },
            "Hub": {
                "id": "Hub",
                "content": [{"type": "text", "value": "Welcome to the hub!"}],
                "choices": [{"text": "Enter Shop", "target": "ShopWelcome"}],
                "execute": [],
            },
            "ShopWelcome": {
                "id": "ShopWelcome",
                "content": [
                    {"type": "text", "value": "Welcome to the shop!"},
                    {"type": "jump", "target": "ShopMenu"},  # Automatic jump
                ],
                "choices": [],
                "execute": [],
            },
            "ShopMenu": {
                "id": "ShopMenu",
                "content": [{"type": "text", "value": "What would you like to buy?"}],
                "choices": [
                    {"text": "Go back to hub", "target": "Hub"},
                    {"text": "Check @prev", "target": "CheckPrev"},
                ],
                "execute": [],
            },
            "CheckPrev": {
                "id": "CheckPrev",
                "content": [{"type": "text", "value": "Checking previous..."}],
                "choices": [{"text": "Go back", "target": "@prev"}],
                "execute": [],
            },
        },
    }


class TestPrevBasicNavigation:
    """Test basic @prev navigation."""

    def test_prev_returns_to_previous_passage(self, prev_story):
        """@prev should navigate to the passage we came from."""
        engine = BardEngine(prev_story)

        # At Start, go to Menu
        engine.choose(0)  # Go to Menu
        assert engine.current_passage_id == "Menu"

        # From Menu, go back
        engine.choose(0)  # Go back via @prev
        assert engine.current_passage_id == "Start"

    def test_prev_tracks_through_multiple_navigations(self, prev_story):
        """@prev should track the most recent passage, not the original."""
        engine = BardEngine(prev_story)

        # Start -> Menu
        engine.choose(0)  # Go to Menu
        assert engine.current_passage_id == "Menu"

        # Menu -> Shop
        engine.choose(1)  # Go to Shop
        assert engine.current_passage_id == "Shop"

        # Shop -> @prev should go to Menu (not Start)
        engine.choose(0)  # Go back via @prev
        assert engine.current_passage_id == "Menu"

    def test_prev_updates_after_each_navigation(self, prev_story):
        """Each navigation should update the previous passage."""
        engine = BardEngine(prev_story)

        # Start -> Menu -> Shop -> @prev (Menu) -> @prev (Shop)
        engine.choose(0)  # Start -> Menu
        engine.choose(1)  # Menu -> Shop
        engine.choose(0)  # Shop -> @prev -> Menu
        assert engine.current_passage_id == "Menu"

        # Now @prev from Menu should go to Shop (since we just came from there)
        engine.choose(0)  # Menu -> @prev -> Shop
        assert engine.current_passage_id == "Shop"


class TestPrevWithJumpChains:
    """Test @prev with automatic jumps (-> in content)."""

    def test_prev_tracks_through_jump_chain(self, jump_chain_story):
        """@prev should track the last passage in a jump chain."""
        engine = BardEngine(jump_chain_story)

        # Start -> Hub
        engine.choose(0)  # Go to Hub
        assert engine.current_passage_id == "Hub"

        # Hub -> ShopWelcome -> ShopMenu (auto-jump)
        engine.choose(0)  # Enter Shop
        # Should end up at ShopMenu due to auto-jump
        assert engine.current_passage_id == "ShopMenu"
        # Previous should be ShopWelcome (the last passage we were at before current)
        assert engine._previous_passage_id == "ShopWelcome"

    def test_prev_from_intermediate_passage(self, jump_chain_story):
        """@prev from a passage reached after a jump chain should go back correctly."""
        engine = BardEngine(jump_chain_story)

        # Navigate: Start -> Hub -> ShopWelcome -> ShopMenu -> CheckPrev
        engine.choose(0)  # Start -> Hub
        engine.choose(0)  # Hub -> ShopWelcome -> ShopMenu (auto-jump)
        engine.choose(1)  # ShopMenu -> CheckPrev
        assert engine.current_passage_id == "CheckPrev"
        assert engine._previous_passage_id == "ShopMenu"

        # @prev from CheckPrev should go to ShopMenu
        engine.choose(0)  # Go back via @prev
        assert engine.current_passage_id == "ShopMenu"


class TestPrevEdgeCases:
    """Test edge cases for @prev."""

    def test_prev_at_start_raises_error(self, prev_story):
        """@prev at the start of a story should raise a clear error."""
        # Create a story that starts with @prev choice
        story = {
            "version": "0.1.0",
            "initial_passage": "Start",
            "passages": {
                "Start": {
                    "id": "Start",
                    "content": [{"type": "text", "value": "Welcome!"}],
                    "choices": [{"text": "Go back", "target": "@prev"}],
                    "execute": [],
                },
            },
        }
        engine = BardEngine(story)

        # Trying to use @prev at the start should raise an error
        with pytest.raises(ValueError) as exc_info:
            engine.choose(0)

        assert "no previous passage exists" in str(exc_info.value)

    def test_prev_via_direct_goto(self, prev_story):
        """@prev should work when called via goto() directly."""
        engine = BardEngine(prev_story)

        # Navigate to Menu
        engine.goto("Menu")
        assert engine.current_passage_id == "Menu"

        # Direct goto to @prev should go back to Start
        engine.goto("@prev")
        assert engine.current_passage_id == "Start"


class TestPrevWithSaveLoad:
    """Test that @prev works correctly with save/load."""

    def test_prev_survives_save_load(self, prev_story):
        """_previous_passage_id should be saved and restored."""
        engine = BardEngine(prev_story)

        # Navigate: Start -> Menu
        engine.choose(0)  # Go to Menu
        assert engine.current_passage_id == "Menu"
        assert engine._previous_passage_id == "Start"

        # Save state
        save_data = engine.save_state()

        # Verify it's in the save data
        assert "previous_passage_id" in save_data
        assert save_data["previous_passage_id"] == "Start"

        # Create a new engine and load state
        engine2 = BardEngine(prev_story)
        engine2.load_state(save_data)

        # Verify previous passage was restored
        assert engine2._previous_passage_id == "Start"

        # @prev should still work
        engine2.choose(0)  # Go back via @prev
        assert engine2.current_passage_id == "Start"


class TestPrevWithUndoRedo:
    """Test that @prev works correctly with undo/redo."""

    def test_prev_survives_undo(self, prev_story):
        """_previous_passage_id should be part of GameSnapshot."""
        engine = BardEngine(prev_story)

        # Navigate: Start -> Menu -> Shop
        engine.choose(0)  # Start -> Menu
        engine.choose(1)  # Menu -> Shop
        assert engine.current_passage_id == "Shop"
        assert engine._previous_passage_id == "Menu"

        # Undo back to Menu
        engine.undo()
        assert engine.current_passage_id == "Menu"
        assert engine._previous_passage_id == "Start"  # Should be restored from snapshot

        # @prev from Menu should go to Start
        engine.choose(0)  # Go back via @prev
        assert engine.current_passage_id == "Start"


class TestPrevParserIntegration:
    """Test that @prev works with compiled .bard files."""

    def test_prev_in_choice_target(self, compile_string):
        """@prev should work as a choice target in .bard files."""
        story = compile_string("""
:: Start
Welcome!
+ [Go to Menu] -> Menu

:: Menu
This is the menu.
+ [Go back] -> @prev
""")
        engine = BardEngine(story)

        # Go to Menu
        engine.choose(0)
        assert engine.current_passage_id == "Menu"

        # Go back via @prev
        engine.choose(0)
        assert engine.current_passage_id == "Start"

    def test_prev_in_jump(self, compile_string):
        """@prev should work as a jump target in .bard files."""
        story = compile_string("""
:: Start
Welcome!
+ [Go to Detour] -> Detour

:: Detour
Taking a detour...
-> @prev
""")
        engine = BardEngine(story)

        # Go to Detour
        engine.choose(0)
        # Should auto-jump back to Start via @prev
        assert engine.current_passage_id == "Start"
