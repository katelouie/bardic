"""Test script for choices in conditionals/loops"""

from bardic.runtime.engine import BardEngine

# Load test story
engine = BardEngine.from_file("test_conditional_choices.json")

print("=" * 60)
print("TEST 1: Start passage (no conditional choices)")
print("=" * 60)
output = engine.current()
print(f"Passage: {output.passage_id}")
print(f"Choices: {len(output.choices)}")
for i, choice in enumerate(output.choices):
    print(f"  {i}. {choice['text']} -> {choice['target']}")

print("\n" + "=" * 60)
print("TEST 2: Simple conditional (has_key=True)")
print("=" * 60)
output = engine.choose(0)  # Go to TestSimple
print(f"Passage: {output.passage_id}")
print(f"Choices: {len(output.choices)}")
for i, choice in enumerate(output.choices):
    print(f"  {i}. {choice['text']} -> {choice['target']}")
print("\nExpected 2 choices: 'Unlock the door', 'Leave it locked'")

print("\n" + "=" * 60)
print("TEST 3: Nested conditionals (has_key=True, has_flashlight=False)")
print("=" * 60)
output = engine.goto("TestNested")
print(f"Passage: {output.passage_id}")
print(f"Choices: {len(output.choices)}")
for i, choice in enumerate(output.choices):
    print(f"  {i}. {choice['text']} -> {choice['target']}")
print("\nExpected 2 choices: 'Unlock in darkness', 'Wait for light'")

print("\n" + "=" * 60)
print("TEST 4: Loop choices (3 inventory items)")
print("=" * 60)
output = engine.goto("TestLoop")
print(f"Passage: {output.passage_id}")
print(f"Choices: {len(output.choices)}")
for i, choice in enumerate(output.choices):
    print(f"  {i}. {choice['text']} -> {choice['target']}")
print("\nExpected 4 choices: 'Use sword', 'Use potion', 'Use rope', 'Back'")

print("\n" + "=" * 60)
print("TEST 5: Mixed passage + conditional (has_flashlight=False)")
print("=" * 60)
output = engine.goto("TestMixed")
print(f"Passage: {output.passage_id}")
print(f"Choices: {len(output.choices)}")
for i, choice in enumerate(output.choices):
    print(f"  {i}. {choice['text']} -> {choice['target']}")
print("\nExpected 2 choices: 'Look around', 'Leave' (NOT 'Search dark corner')")

print("\n" + "=" * 60)
print("TEST 6: Mixed with condition TRUE")
print("=" * 60)
engine.state['has_flashlight'] = True
output = engine.goto("TestMixed")
print(f"Passage: {output.passage_id}")
print(f"Choices: {len(output.choices)}")
for i, choice in enumerate(output.choices):
    print(f"  {i}. {choice['text']} -> {choice['target']}")
print("\nExpected 3 choices: 'Look around', 'Search dark corner', 'Leave'")

print("\n" + "=" * 60)
print("✓ ALL TESTS COMPLETED!")
print("=" * 60)
