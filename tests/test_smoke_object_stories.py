"""
Smoke tests for test stories that use custom Python objects.

These tests verify that stories with game_logic imports can:
1. Compile successfully
2. Load into the BardEngine
3. Execute at least the first passage without errors
"""

import pytest
import json
from pathlib import Path
from bardic.compiler.compiler import BardCompiler
from bardic.runtime.engine import BardEngine


# List of test stories that use game_logic objects
OBJECT_STORIES = [
    "test_loop_objects.bard",
    "test_full_reading.bard",
    "test_conditional_objects.bard",
    "test_render_directives.bard",
    "test_render_demo.bard",
]


@pytest.mark.parametrize("story_filename", OBJECT_STORIES)
def test_object_story_smoke(story_filename, tmp_path):
    """
    Smoke test: Compile and load a story with custom objects.

    This test verifies:
    - The story compiles without errors
    - The compiled JSON is valid
    - The engine can load the story
    - The first passage can be rendered
    """
    # Path to test story
    story_path = Path("stories/test") / story_filename
    output_path = tmp_path / f"{story_filename}.json"

    # 1. Compile
    compiler = BardCompiler()
    compiled_path = compiler.compile_file(str(story_path), str(output_path))
    assert Path(compiled_path).exists(), f"Compilation failed for {story_filename}"

    # 2. Load JSON
    with open(compiled_path) as f:
        story_data = json.load(f)
    assert "passages" in story_data, f"No passages in {story_filename}"

    # 3. Create engine
    engine = BardEngine(story_data)
    assert engine is not None, f"Failed to create engine for {story_filename}"

    # 4. Render first passage (this executes imports and Python blocks)
    output = engine.current()
    assert output.passage_id is not None, f"No passage ID for {story_filename}"
    assert output.content is not None, f"No content rendered for {story_filename}"

    print(f"✓ {story_filename}: {len(story_data['passages'])} passages, first passage OK")


def test_card_class_methods():
    """Test that the Card class has all expected methods."""
    from game_logic.test_tarot_objects import Card

    card = Card("The Fool", 0, False)

    # Test attributes
    assert card.name == "The Fool"
    assert card.number == 0
    assert card.reversed is False
    assert card.position is None

    # Test methods
    assert card.is_major_arcana() is True
    assert "The Fool" in card.get_display_name()

    # Test position setting
    card.in_position("past")
    assert card.position == "past"
    assert "shaped you" in card.get_position_meaning()


def test_client_class_methods():
    """Test that the Client class has all expected methods."""
    from game_logic.test_tarot_objects import Client, Card

    client = Client("Test Client", 30)

    # Test attributes
    assert client.name == "Test Client"
    assert client.age == 30
    assert client.trust_level == 50  # Default

    # Test trust modification
    client.modify_trust(20)
    assert client.trust_level == 70

    client.modify_trust(-30)
    assert client.trust_level == 40

    # Test bounds (0-100)
    client.modify_trust(-100)
    assert client.trust_level == 0

    client.modify_trust(200)
    assert client.trust_level == 100

    # Test card tracking
    card = Card("The Fool", 0, False)
    client.add_card_seen(card)
    assert len(client.cards_seen) == 1

    # Test trust description
    desc = client.get_trust_description()
    assert isinstance(desc, str)
    assert len(desc) > 0


def test_reader_class_methods():
    """Test that the Reader class has all expected methods."""
    from game_logic.test_tarot_objects import Reader

    reader = Reader("Test Reader")

    # Test attributes
    assert reader.name == "Test Reader"
    assert reader.experience == 0

    # Test experience
    reader.add_experience(50)
    assert reader.experience == 50

    # Test leveling (100 exp per level)
    assert reader.get_level() == 0

    reader.add_experience(100)
    assert reader.get_level() == 1

    reader.add_experience(150)
    assert reader.get_level() == 3  # 300 total


def test_draw_cards_function():
    """Test that draw_cards() returns valid cards."""
    from game_logic.test_tarot_objects import draw_cards

    cards = draw_cards(5)

    # Should return a list
    assert isinstance(cards, list)
    assert len(cards) == 5

    # Each should be a Card
    for card in cards:
        assert hasattr(card, "name")
        assert hasattr(card, "reversed")
        assert hasattr(card, "is_major_arcana")

    # Draw different count
    cards = draw_cards(10)
    assert len(cards) == 10
