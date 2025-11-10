"""Test choice text interpolation"""

from bardic.runtime.engine import BardEngine

# Load test story
engine = BardEngine.from_file("test_interpolation.json")

print("=" * 60)
print("TEST: Choice text interpolation")
print("=" * 60)
output = engine.current()
print(f"Passage: {output.passage_id}")
print(f"\nChoices ({len(output.choices)}):")
for i, choice in enumerate(output.choices):
    print(f"  {i}. {choice['text']} -> {choice['target']}")

print("\n" + "=" * 60)
print("Expected:")
print("  0. Pick up the Mysterious Key")
print("  1. Take 5 gold coins")
print("  2. Buy for 42.50 silver")
print("  3. See inventory")
print("=" * 60)

print("\n" + "=" * 60)
print("TEST: Loop choice interpolation")
print("=" * 60)
output = engine.choose(3)  # Go to ShowInventory
print(f"Passage: {output.passage_id}")
print(f"\nChoices ({len(output.choices)}):")
for i, choice in enumerate(output.choices):
    print(f"  {i}. {choice['text']} -> {choice['target']}")

print("\n" + "=" * 60)
print("Expected:")
print("  0. Use Sword of Light")
print("  1. Use Healing Potion")
print("  2. Use Magic Rope")
print("  3. Back")
print("=" * 60)

print("\n✓ ALL TESTS COMPLETED!")
