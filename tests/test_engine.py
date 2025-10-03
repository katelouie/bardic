"""Manual test of the runtime engine."""

import json
from bardic.runtime.engine import BardEngine

def test_basic_navigation():
    """Test basic story navigation"""

    # Load the compiled story
    with open('test_story.json') as f:
        story = json.load(f)

    # Create engine
    engine = BardEngine(story)

    # Show story info
    info = engine.get_story_info()
    print("Story Info:")
    print(f"  Version: {info['version']}")
    print(f"  Passages: {info['passage_count']}")
    print(f"  Starting at: {info['initial_passage']}")
    print()

    # Get first passage
    output = engine.current()
    print(f"=== {output.passage_id} ===")
    print(output.content)
    print()
    print("Choices:")
    for i, choice in enumerate(output.choices):
        print(f"  {i}: {choice['text']} -> {choice['target']}")
    print()

    # Make a choice
    print("Choosing option 0...")
    output = engine.choose(0)
    print()

    print(f"=== {output.passage_id} ===")
    print(output.content)
    print()
    print("Choices:")
    for i, choice in enumerate(output.choices):
        print(f"  {i}: {choice['text']} -> {choice['target']}")
    print()

    # Navigate manually
    print("Navigating to ExamineScratches...")
    engine.goto('ExamineScratches')
    output = engine.current()
    print()

    print(f"=== {output.passage_id} ===")
    print(output.content)
    print()


def test_error_handling():
    """Test error handling"""

    with open('test_story.json') as f:
        story = json.load(f)

    engine = BardEngine(story)

    # Test invalid passage
    try:
        engine.goto('NonExistentPassage')
        print("ERROR: Should have raised ValueError")
    except ValueError as e:
        print(f"✓ Caught expected error: {e}")

    # Test invalid choice
    try:
        engine.choose(999)
        print("ERROR: Should have raised IndexError")
    except IndexError as e:
        print(f"✓ Caught expected error: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Basic Navigation")
    print("=" * 60)
    test_basic_navigation()

    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    test_error_handling()

    print("\n✅ All tests passed!")