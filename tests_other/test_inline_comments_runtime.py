"""Test that inline comments work correctly at runtime."""

import sys
sys.path.insert(0, '/Users/katelouie/code/bardic')

from bardic.runtime.engine import BardEngine

print("=== Testing inline comments runtime ===\n")

# Load the test story
engine = BardEngine.from_file("test_inline_comments.json")

# Set up state
engine.state["health"] = 60
engine.state["variable"] = "test_value"
engine.state["items"] = ["Sword", "Shield", "Potion"]

# Navigate to start
output = engine.goto("Start")

print(f"Content length: {len(output.content)}")
print(f"Has choices: {len(output.choices) > 0}")

# Verify comments don't leak into content
assert "// " not in output.content, "Comment leaked into content!"
assert "this is ignored" not in output.content, "Comment text leaked!"
assert "high health check" not in output.content, "Comment text leaked!"

# Verify escaped slashes work
print("\n=== Testing escaping ===")
engine2 = BardEngine.from_file("test_comment_escaping.json")
output2 = engine2.goto("Start")

print(f"Content preview:\n{output2.content[:200]}")

# Verify literal // appears
assert "https://example.com" in output2.content, "Escaped slashes not working!"
assert "just slashes" in output2.content, "Escaped text missing!"

print("\n✓ All runtime tests passed!")
print("✓ Comments properly stripped")
print("✓ Escaped slashes work correctly")
